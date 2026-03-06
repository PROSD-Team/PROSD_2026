#!/usr/bin/env python3
"""
TODO: REMOVE THIS. This is just an example of event emitting, should not get into any form of final version
"""

import os
import sys
import json
import time
import logging
import signal
from datetime import datetime, timezone
from typing import Optional, Dict, Any

# ═══════════════════════════════════════════════════════════════
# FEATURE FLAGS (from environment)
# ═══════════════════════════════════════════════════════════════
ENABLE_METRICS = os.getenv('ENABLE_METRICS', 'true').lower() == 'true'
ENABLE_LOGGING = os.getenv('ENABLE_LOGGING', 'true').lower() == 'true'

# Conditional imports for observability
if ENABLE_METRICS:
    from prometheus_client import start_http_server, Counter, Histogram, Gauge

# ═══════════════════════════════════════════════════════════════
# PROMETHEUS METRICS DEFINITIONS
# ═══════════════════════════════════════════════════════════════
if ENABLE_METRICS:
    JOB_PROCESSED = Counter(
        'jobs_processed_total',
        'Total jobs processed by Python service',
        ['status', 'job_type']
    )
    
    JOB_DURATION = Histogram(
        'job_processing_seconds',
        'Time spent processing a job',
        ['job_type'],
        buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, float('inf')]
    )
    
    QUEUE_DEPTH = Gauge(
        'rabbitmq_queue_depth',
        'Current depth of the job queue',
        ['queue_name']
    )
    
    ACTIVE_WORKERS = Gauge(
        'active_workers',
        'Number of active worker processes'
    )
    
    DB_OPERATIONS = Counter(
        'database_operations_total',
        'Database operations performed',
        ['operation', 'status']
    )
    
    MINIO_OPERATIONS = Counter(
        'minio_operations_total',
        'MinIO object storage operations',
        ['operation', 'status']
    )

# ═══════════════════════════════════════════════════════════════
# LOGGING CONFIGURATION
# ═══════════════════════════════════════════════════════════════
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console handler (always enabled) - structured JSON output
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))
logger.addHandler(console_handler)

# ═══════════════════════════════════════════════════════════════
# LOKI LOGGING CONFIGURATION
# ═══════════════════════════════════════════════════════════════
if ENABLE_LOGGING:
    try:
        import logging
        import logging_loki  # correct import path
        from logging_loki import LokiHandler

        loki_url = os.getenv("LOKI_URL", "http://loki:3100")
        service_name = os.getenv("COMPOSE_PROJECT_NAME", "prosd").replace("-", "_")

        loki_handler = LokiHandler(
            url=f"{loki_url}/loki/api/v1/push",
            tags={
                "app": "python-service",
                "service": f"{service_name}_algorithm",
                "environment": os.getenv("ASPNETCORE_ENVIRONMENT", "development"),
                "hostname": os.getenv("HOSTNAME", "unknown"),
            },
            version="1",  # Loki API version (1 for older Loki)
        )

        # JSON formatter for structured logs
        from pythonjsonlogger import jsonlogger
        json_formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        loki_handler.setFormatter(json_formatter)

        logger.addHandler(loki_handler)
        logger.info("✅ Loki logging enabled (python-logging-loki)")

    except ImportError as e:
        logger.warning(f"⚠️ Loki handler not available: {type(e).__name__}: {e}")
        logger.warning("⚠️ Logging will only go to console")
    except Exception as e:
        logger.warning(f"⚠️ Could not initialize Loki handler: {type(e).__name__}: {e}")
        logger.warning("⚠️ Falling back to console only")


# ═══════════════════════════════════════════════════════════════
# GLOBAL STATE
# ═══════════════════════════════════════════════════════════════
_shutdown_requested = False

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    global _shutdown_requested
    sig_name = signal.Signals(signum).name
    logger.info(f"👋 Received {sig_name}, initiating graceful shutdown...")
    _shutdown_requested = True

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ═══════════════════════════════════════════════════════════════
# BUSINESS LOGIC
# ═══════════════════════════════════════════════════════════════
def process_algorithm_task(task: Dict[str, Any]) -> bool:
    """
    Process a single algorithm task from the queue.
    
    Args:
        task: Dictionary containing task data with keys:
            - id: Unique task identifier
            - type: Task type/category
            - data: Task payload
            - priority: Optional priority level
            
    Returns:
        bool: True if processing succeeded, False otherwise
    """
    start_time = time.time()
    task_id = task.get('id', 'unknown')
    job_type = task.get('type', 'unknown')
    priority = task.get('priority', 'normal')
    
    logger.info(f"🔄 Processing task {task_id} (type: {job_type}, priority: {priority})")
    
    try:
        # === YOUR ALGORITHM LOGIC HERE ===
        # Example: Simulate processing with variable duration based on priority
        process_time = 0.1 if priority == 'high' else 0.5
        time.sleep(process_time)
        
        # Example: Transform input data
        input_data = task.get('data', {})
        result = {
            'task_id': task_id,
            'status': 'completed',
            'output': {
                'processed': True,
                'input_hash': hash(json.dumps(input_data, sort_keys=True)),
                'result_data': f"Processed {len(str(input_data))} bytes",
                'metadata': {
                    'processed_at': datetime.now(timezone.utc).isoformat(),
                    'worker_id': os.getenv('HOSTNAME', 'unknown'),
                    'version': '1.0.0'
                }
            }
        }
        # === END ALGORITHM LOGIC ===
        
        # Record success metrics
        if ENABLE_METRICS:
            JOB_PROCESSED.labels(status='success', job_type=job_type).inc()
            JOB_DURATION.labels(job_type=job_type).observe(time.time() - start_time)
        
        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"✅ Task {task_id} completed in {elapsed_ms:.1f}ms")
        return True
        
    except ConnectionError as e:
        # Handle transient errors that might benefit from retry
        if ENABLE_METRICS:
            JOB_PROCESSED.labels(status='retryable_error', job_type=job_type).inc()
        logger.warning(f"⚠️ Task {task_id} retryable error: {e}")
        return False
        
    except Exception as e:
        # Handle permanent errors
        if ENABLE_METRICS:
            JOB_PROCESSED.labels(status='failed', job_type=job_type).inc()
        
        error_type = type(e).__name__
        logger.error(f"❌ Task {task_id} failed [{error_type}]: {str(e)}", exc_info=True)
        return False


def save_result_to_postgres(task_id: str, result: Dict[str, Any]) -> bool:
    """
    Save processing result to PostgreSQL database.
    
    Args:
        task_id: Task identifier
        result: Processing result dictionary
        
    Returns:
        bool: True if save succeeded, False otherwise
    """
    try:
        # === DATABASE SAVE LOGIC HERE ===
        # Example using SQLAlchemy (pseudo-code):
        # from sqlalchemy.orm import Session
        # with Session(engine) as session:
        #     record = JobResult(task_id=task_id, result=result, created_at=datetime.utcnow())
        #     session.add(record)
        #     session.commit()
        
        if ENABLE_METRICS:
            DB_OPERATIONS.labels(operation='insert', status='success').inc()
        
        logger.debug(f"💾 Saved result for task {task_id} to PostgreSQL")
        return True
        
    except Exception as e:
        if ENABLE_METRICS:
            DB_OPERATIONS.labels(operation='insert', status='failed').inc()
        logger.error(f"❌ Failed to save task {task_id} to database: {e}", exc_info=True)
        return False


def save_file_to_minio(task_id: str, filename: str, content: bytes) -> Optional[str]:
    """
    Save file to MinIO object storage.
    
    Args:
        task_id: Task identifier
        filename: Desired filename in storage
        content: File content as bytes
        
    Returns:
        str: Object key/path if successful, None otherwise
    """
    try:
        # === MINIO SAVE LOGIC HERE ===
        # Example using minio library (pseudo-code):
        # from minio import Minio
        # client = Minio(
        #     os.getenv('MINIO_ENDPOINT', 'minio:9000'),
        #     access_key=os.getenv('MINIO_ACCESS_KEY'),
        #     secret_key=os.getenv('MINIO_SECRET_KEY'),
        #     secure=False
        # )
        # object_name = f"results/{task_id}/{filename}"
        # client.put_object(
        #     bucket_name=os.getenv('MINIO_BUCKET', 'prosd-files'),
        #     object_name=object_name,
        #     data=io.BytesIO(content),
        #     length=len(content)
        # )
        
        object_key = f"results/{task_id}/{filename}"
        
        if ENABLE_METRICS:
            MINIO_OPERATIONS.labels(operation='put_object', status='success').inc()
        
        logger.debug(f"📦 Saved file {filename} to MinIO: {object_key}")
        return object_key
        
    except Exception as e:
        if ENABLE_METRICS:
            MINIO_OPERATIONS.labels(operation='put_object', status='failed').inc()
        logger.error(f"❌ Failed to save file to MinIO: {e}", exc_info=True)
        return None


def health_check() -> Dict[str, Any]:
    """
    Health check endpoint for Docker/Kubernetes probes.
    
    Returns:
        dict: Health status information
    """
    health = {
        'status': 'healthy',
        'service': 'prosd-python-algorithm',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'uptime_seconds': time.time() - _start_time,
        'metrics_enabled': ENABLE_METRICS,
        'logging_enabled': ENABLE_LOGGING,
        'shutdown_requested': _shutdown_requested
    }
    
    # Add dependency checks if needed:
    # health['postgres'] = check_postgres_connection()
    # health['rabbitmq'] = check_rabbitmq_connection()
    # health['minio'] = check_minio_connection()
    
    return health


def check_postgres_connection() -> bool:
    """Check PostgreSQL connectivity (placeholder)"""
    # Implement actual connection check with psycopg2/sqlalchemy
    return True


def check_rabbitmq_connection() -> bool:
    """Check RabbitMQ connectivity (placeholder)"""
    # Implement actual connection check with pika
    return True


def check_minio_connection() -> bool:
    """Check MinIO connectivity (placeholder)"""
    # Implement actual connection check with minio library
    return True

# ═══════════════════════════════════════════════════════════════
# RABBITMQ CONSUMER
# ═══════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════
# RABBITMQ CONSUMER (Production Implementation)
# ═══════════════════════════════════════════════════════════════

def setup_rabbitmq_consumer(max_retries: int = 10, retry_delay: float = 2.0):
    """
    Setup and start RabbitMQ consumer with retry logic and dead-letter handling.
    
    Args:
        max_retries: Maximum connection attempts before giving up
        retry_delay: Base delay between retries (exponential backoff)
    
    Returns:
        tuple: (connection, channel) or (None, None) if setup failed
    """
    try:
        import pika
        from pika.exceptions import AMQPConnectionError, AMQPChannelError, ConnectionClosedByBroker
    except ImportError:
        logger.warning("⚠️ pika not installed - RabbitMQ consumer disabled")
        logger.warning("⚠️ Install with: pip install pika")
        return None, None

    # Connection parameters from environment
    rabbit_host = os.getenv('RABBITMQ_HOST', 'rabbitmq')
    rabbit_port = int(os.getenv('RABBITMQ_PORT', '5672'))
    rabbit_user = os.getenv('RABBITMQ_USER', 'guest')
    rabbit_pass = os.getenv('RABBITMQ_PASS', 'guest')
    rabbit_vhost = os.getenv('RABBITMQ_VHOST', '/')
    queue_name = os.getenv('RABBITMQ_QUEUE', 'prosd-jobs')
    
    # DLQ configuration
    dlq_exchange = os.getenv('RABBITMQ_DLQ_EXCHANGE', 'prosd-dlq')
    dlq_queue = os.getenv('RABBITMQ_DLQ_QUEUE', 'prosd-dlq-queue')
    max_message_retries = int(os.getenv('RABBITMQ_MAX_RETRIES', '3'))
    
    credentials = pika.PlainCredentials(rabbit_user, rabbit_pass)
    
    # Connection parameters with timeouts
    parameters = pika.ConnectionParameters(
        host=rabbit_host,
        port=rabbit_port,
        virtual_host=rabbit_vhost,
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300,
        connection_attempts=3,      # Built-in pika retries
        retry_delay=2,              # Seconds between built-in attempts
        socket_timeout=10,
        client_properties={
            'connection_name': f'prosd-python-service-{os.getenv("HOSTNAME", "unknown")}'
        }
    )

    # Retry loop with exponential backoff
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"🔗 Attempting RabbitMQ connection ({attempt}/{max_retries}) to {rabbit_host}:{rabbit_port}...")
            
            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            
            # Enable publisher confirms for reliability
            channel.confirm_delivery()
            
            # Declare Dead Letter Exchange and Queue
            channel.exchange_declare(
                exchange=dlq_exchange,
                exchange_type='direct',
                durable=True
            )
            channel.queue_declare(
                queue=dlq_queue,
                durable=True,
                arguments={
                    'x-message-ttl': 86400000,  # 24 hours retention in DLQ
                    'x-max-length': 10000        # Max 10k messages in DLQ
                }
            )
            channel.queue_bind(
                queue=dlq_queue,
                exchange=dlq_exchange,
                routing_key='prosd.failed'
            )
            
            # Declare main queue with DLQ arguments
            channel.queue_declare(
                queue=queue_name,
                durable=True,
                arguments={
                    'x-dead-letter-exchange': dlq_exchange,
                    'x-dead-letter-routing-key': 'prosd.failed',
                    'x-max-priority': 10,  # Enable priority queue
                    'x-message-ttl': 3600000  # 1 hour TTL for messages in queue
                }
            )
            
            # Prefetch to control load (1 = process one message at a time)
            channel.basic_qos(prefetch_count=1)
            
            # Define message callback with retry tracking
            def on_message(channel, method, properties, body):
                """Callback for received messages with retry logic"""
                # Extract retry count from headers
                retry_count = 0
                if properties.headers and 'x-retry-count' in properties.headers:
                    retry_count = properties.headers['x-retry-count']
                
                task_id = 'unknown'
                try:
                    task = json.loads(body)
                    task_id = task.get('id', 'unknown')
                    job_type = task.get('type', 'unknown')
                    
                    logger.debug(f"📥 Received task {task_id} (attempt {retry_count + 1}/{max_message_retries + 1})")
                    
                    # Process the task
                    success = process_algorithm_task(task)
                    
                    if success:
                        channel.basic_ack(delivery_tag=method.delivery_tag)
                        logger.info(f"✅ Task {task_id} acknowledged successfully")
                        
                        # Update metrics
                        if ENABLE_METRICS:
                            JOB_PROCESSED.labels(status='success', job_type=job_type).inc()
                    else:
                        # Task processing failed - decide whether to retry or DLQ
                        _handle_message_failure(
                            channel=channel,
                            method=method,
                            properties=properties,
                            body=body,
                            retry_count=retry_count,
                            max_retries=max_message_retries,
                            dlq_exchange=dlq_exchange,
                            task_id=task_id,
                            reason='processing_failed'
                        )
                        
                except json.JSONDecodeError as e:
                    # Malformed JSON - never retry, send to DLQ
                    logger.error(f"❌ Invalid JSON in message: {body[:200]}... Error: {e}")
                    channel.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
                    
                    # Publish to DLQ for debugging
                    _publish_to_dlq(
                        channel=channel,
                        body=body,
                        properties=properties,
                        dlq_exchange=dlq_exchange,
                        reason=f'json_parse_error: {str(e)[:100]}',
                        task_id='parse_error'
                    )
                    
                except ConnectionError as e:
                    # Transient connection issue - requeue without incrementing retry count
                    logger.warning(f"⚠️ Transient connection error: {e}. Requeuing without retry penalty.")
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    
                except Exception as e:
                    # Unexpected error - decide based on retry count
                    error_type = type(e).__name__
                    logger.error(f"❌ Error processing message {task_id}: {error_type}: {str(e)[:100]}", exc_info=True)
                    
                    _handle_message_failure(
                        channel=channel,
                        method=method,
                        properties=properties,
                        body=body,
                        retry_count=retry_count,
                        max_retries=max_message_retries,
                        dlq_exchange=dlq_exchange,
                        task_id=task_id,
                        reason=f'{error_type}: {str(e)[:50]}'
                    )
            
            # Start consuming
            channel.basic_consume(
                queue=queue_name,
                on_message_callback=on_message,
                auto_ack=False  # Manual acknowledgment required
            )
            
            logger.info(f"✅ RabbitMQ consumer started successfully")
            logger.info(f"   📍 Host: {rabbit_host}:{rabbit_port}")
            logger.info(f"   📍 Queue: {queue_name}")
            logger.info(f"   📍 DLQ: {dlq_queue}")
            logger.info(f"   📍 Max Retries: {max_message_retries}")
            
            return connection, channel
            
        except (AMQPConnectionError, AMQPChannelError, ConnectionClosedByBroker) as e:
            if attempt == max_retries:
                logger.error(f"❌ Failed to connect to RabbitMQ after {max_retries} attempts: {e}")
                return None, None
            
            wait_time = retry_delay * (2 ** (attempt - 1))  # Exponential backoff
            logger.warning(f"⚠️ Connection attempt {attempt} failed: {type(e).__name__}: {e}. Retrying in {wait_time:.1f}s...")
            time.sleep(wait_time)
            
        except Exception as e:
            logger.error(f"❌ Unexpected error setting up RabbitMQ consumer: {type(e).__name__}: {e}", exc_info=True)
            return None, None
    
    return None, None


def _handle_message_failure(channel, method, properties, body, retry_count, 
                           max_retries, dlq_exchange, task_id: str, reason: str):
    """
    Helper: either requeue with incremented retry count, or route to DLQ.
    """
    delivery_tag = method.delivery_tag
    
    if retry_count < max_retries:
        # Requeue with incremented retry count
        new_headers = dict(properties.headers or {})
        new_headers['x-retry-count'] = retry_count + 1
        new_headers['x-last-error'] = reason
        new_headers['x-retry-at'] = datetime.now(timezone.utc).isoformat()
        
        # Republish with headers
        channel.basic_publish(
            exchange=properties.exchange or '',
            routing_key=properties.routing_key or '',
            body=body,
            properties=pika.BasicProperties(
                headers=new_headers,
                delivery_mode=2,  # persistent
                priority=properties.priority
            )
        )
        logger.warning(f"⚠️ Task {task_id} requeued (attempt {retry_count + 2}/{max_retries + 1}). Reason: {reason}")
        channel.basic_ack(delivery_tag=delivery_tag)  # Ack original to remove it
        
    else:
        # Max retries exceeded → route to Dead Letter Queue
        logger.error(f"🪦 Task {task_id} exceeded max retries ({max_retries}). Routing to DLQ. Reason: {reason}")
        
        _publish_to_dlq(
            channel=channel,
            body=body,
            properties=properties,
            dlq_exchange=dlq_exchange,
            reason=reason,
            task_id=task_id,
            retry_count=retry_count
        )
        channel.basic_ack(delivery_tag=delivery_tag)


def _publish_to_dlq(channel, body, properties, dlq_exchange: str, 
                    reason: str, task_id: str, retry_count: int = 0):
    """
    Publish failed message to Dead Letter Queue with diagnostic headers.
    """
    try:
        dlq_headers = dict(properties.headers or {})
        dlq_headers.update({
            'x-dlq-reason': reason,
            'x-dlq-original-exchange': properties.exchange,
            'x-dlq-original-routing-key': properties.routing_key,
            'x-dlq-failed-at': datetime.now(timezone.utc).isoformat(),
            'x-retry-count': retry_count,
            'x-task-id': task_id
        })
        
        channel.basic_publish(
            exchange=dlq_exchange,
            routing_key='prosd.failed',
            body=body,
            properties=pika.BasicProperties(
                headers=dlq_headers,
                delivery_mode=2,
                priority=properties.priority
            )
        )
        logger.info(f"📦 Message published to DLQ: task_id={task_id}")
        
    except Exception as e:
        logger.error(f"❌ Failed to publish to DLQ: {e}", exc_info=True)


# ═══════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════
_start_time = time.time()

def main():
    """Main application entry point"""
    global _start_time
    
    # Start Prometheus metrics server if enabled
    if ENABLE_METRICS:
        metrics_port = int(os.getenv('METRICS_PORT', '8000'))
        try:
            start_http_server(metrics_port)
            logger.info(f"📊 Prometheus metrics server started on port {metrics_port}")
            logger.info(f"📊 Metrics endpoint: http://localhost:{metrics_port}/metrics")
        except Exception as e:
            logger.error(f"❌ Failed to start metrics server: {e}")
    
    # Initialize worker metrics
    if ENABLE_METRICS:
        ACTIVE_WORKERS.set(1)
        QUEUE_DEPTH.labels(queue_name=os.getenv('RABBITMQ_QUEUE', 'prosd-jobs')).set(0)
    
    # Startup logging
    logger.info("🚀 PROSD Python Algorithm Service starting...")
    logger.info(f"   Environment: {os.getenv('ASPNETCORE_ENVIRONMENT', 'development')}")
    logger.info(f"   Hostname: {os.getenv('HOSTNAME', 'unknown')}")
    logger.info(f"   Metrics: {'✅ Enabled' if ENABLE_METRICS else '❌ Disabled'}")
    logger.info(f"   Logging: {'✅ Enabled' if ENABLE_LOGGING else '❌ Disabled'}")
    logger.info(f"   PID: {os.getpid()}")
    
    # Setup RabbitMQ consumer (production mode)
    connection, channel = setup_rabbitmq_consumer()
    
    # Development mode: simulate work if no RabbitMQ
    if connection is None:
        logger.info("🧪 Running in development mode (no RabbitMQ connection)")
        logger.info("💡 To enable RabbitMQ: pip install pika and set RABBITMQ_* env vars")
    
    try:
        # Main processing loop
        while not _shutdown_requested:
            if connection and channel:
                # Production: RabbitMQ handles callbacks, just process events
                connection.process_data_events(time_limit=1)
            else:
                # Development: simulate periodic work
                simulate_development_task()
            
            # Update queue depth metric periodically
            if ENABLE_METRICS and not _shutdown_requested:
                update_queue_depth_metric()
                
    except KeyboardInterrupt:
        logger.info("👋 Received keyboard interrupt")
    except Exception as e:
        logger.error(f"❌ Fatal error in main loop: {type(e).__name__}: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Graceful shutdown
        shutdown(connection, channel)
    
    logger.info("🛑 Service stopped")
    return 0


def simulate_development_task():
    """Simulate a task in development mode (no RabbitMQ)"""
    # Create a sample task every 10 seconds
    if int(time.time()) % 10 == 0:
        sample_task = {
            'id': f'dev-task-{int(time.time())}',
            'type': 'sample',
            'priority': 'normal',
            'data': {'sample': True, 'timestamp': datetime.now(timezone.utc).isoformat()}
        }
        success = process_algorithm_task(sample_task)
        if success:
            # Simulate saving results
            save_result_to_postgres(sample_task['id'], {'result': 'ok'})
            save_file_to_minio(sample_task['id'], 'output.json', b'{"status":"ok"}')
    time.sleep(1)


def update_queue_depth_metric():
    """Update queue depth metric from RabbitMQ"""
    if ENABLE_METRICS:
        try:
            # In production, query RabbitMQ HTTP API for queue depth
            # import requests
            # response = requests.get(
            #     f"http://{os.getenv('RABBITMQ_HOST', 'rabbitmq')}:15672/api/queues/%2F/{queue_name}",
            #     auth=(os.getenv('RABBITMQ_USER'), os.getenv('RABBITMQ_PASS'))
            # )
            # if response.ok:
            #     depth = response.json().get('messages_ready', 0)
            #     QUEUE_DEPTH.labels(queue_name=queue_name).set(depth)
            pass  # Placeholder for actual implementation
        except Exception as e:
            logger.debug(f"Could not update queue depth metric: {e}")


def shutdown(connection, channel):
    """Graceful shutdown procedure"""
    logger.info("🔌 Shutting down...")
    
    # Update metrics
    if ENABLE_METRICS:
        ACTIVE_WORKERS.set(0)
    
    # Close RabbitMQ connection
    if channel:
        try:
            channel.close()
            logger.debug("🔌 RabbitMQ channel closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing channel: {e}")
    
    if connection and connection.is_open:
        try:
            connection.close()
            logger.debug("🔌 RabbitMQ connection closed")
        except Exception as e:
            logger.warning(f"⚠️ Error closing connection: {e}")
    
    # Flush logs
    for handler in logger.handlers:
        handler.flush()
    
    logger.info("✅ Shutdown complete")


if __name__ == '__main__':
    sys.exit(main())