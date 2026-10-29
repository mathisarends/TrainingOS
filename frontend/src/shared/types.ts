/** Domain-facing aliases of the OpenAPI-generated contracts. No handwritten DTOs. */
export type { UserResponse as User } from '../api/generated/users/models';
export type {
  ExerciseResponse as Exercise,
  Category,
  CategoryDefaultsResponse as CategoryDefaults,
} from '../api/generated/exercises/models';
export type {
  PrescriptionResponse as Prescription,
  SlotResponse as PlanSlot,
  DayResponse as TrainingDay,
  PlanResponse as Plan,
  NextTrainingResponse as NextTraining,
  ProgressionPreviewResponse as ProgressionPreview,
} from '../api/generated/plans/models';
export type {
  WorkSetResponse as WorkSet,
  TrainingSessionSlotResponse as TrainingSlot,
  TrainingSessionResponse as TrainingSession,
  GuidanceResponse as Guidance,
  SetFeedbackResponse as SetFeedback,
} from '../api/generated/training-sessions/models';
export type Decimal = string;

/** Local preview/test boundary; production HTTP uses lit-canon-fetch. */
export interface Transport {
  request<T>(
    path: string,
    method?: string,
    body?: unknown,
    options?: Omit<RequestInit, 'method' | 'body'>,
  ): Promise<T>;
}
