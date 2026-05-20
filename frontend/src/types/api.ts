// Опис алгоритму з метаданих
export interface Algorithm {
    id: string;
    name: string;
    description: string;
    category: string;
}

// Група категорій алгоритмів
export interface CategoryGroup {
    category: string;
    algorithms: Algorithm[];
}

// Тіло запиту для створення Job-а
export interface CreateJobRequest {
    pipelineSteps: string;  // Серіалізований JSON масив кроків
    connectionId: string;   // ID підключення SignalR (важливо!)
    parametersJson: string; // Серіалізований JSON параметрів
    targetWorker?: string;  // Опціонально — цільовий воркер
    userId?: string;
    pipelineId?: number;
}

// Відповідь статусу Job-а
export interface JobStatusResponse {
    jobId: number;
    status: string;
    currentStep: number;
    targetWorker: string | null;
}

export interface RegisterResponse {
    id: string;
    email: string;
}

export interface PipelineSummary {
    id: number;
    name: string;
    definitionJson: string;
    parentPipelineId: number | null;
    createdAt: string;
    updatedAt: string;
}

export interface JobHistoryEntry {
    jobId: number;
    status: string;
    pipelineSteps: string;
    pipelineId?: number | null;
    pipelineName?: string | null;
    createdAt: string;
}
