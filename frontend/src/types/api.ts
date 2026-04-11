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
}

// Відповідь статусу Job-а
export interface JobStatusResponse {
    jobId: number;
    status: string;
    currentStep: number;
    targetWorker: string | null;
}
