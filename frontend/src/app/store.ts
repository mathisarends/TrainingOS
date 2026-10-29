import { QueryClient } from '@tanstack/lit-query';
import { auth, exercises, plans, trainingSessions } from '../api/generated';

/** App-scoped server state. A user change always clears every cached resource. */
export class TrainingStore {
  constructor(private readonly client: QueryClient) {}

  async user() {
    return this.client.fetchQuery(auth.getAuthenticatedUserQuery());
  }

  async dashboard() {
    await Promise.all([
      this.client.invalidateQueries({ queryKey: plans.plansKeys.all, refetchType: 'none' }),
      this.client.invalidateQueries({ queryKey: exercises.exercisesKeys.all, refetchType: 'none' }),
      this.client.invalidateQueries({
        queryKey: trainingSessions.trainingSessionsKeys.all,
        refetchType: 'none',
      }),
    ]);
    const [planList, catalog, history, next] = await Promise.all([
      this.client.fetchQuery(plans.listPlansQuery()),
      this.client.fetchQuery(exercises.listExercisesQuery()),
      this.client.fetchQuery(trainingSessions.listTrainingSessionsQuery({ limit: 100 })),
      this.client.fetchQuery(plans.getNextTrainingQuery()),
    ]);
    // Plan progress needs the complete recorded history.
    const sessions = [...history.items];
    let pageSize = history.items.length;
    while (pageSize === 100) {
      const page = await this.client.fetchQuery(
        trainingSessions.listTrainingSessionsQuery({ offset: sessions.length, limit: 100 }),
      );
      sessions.push(...page.items);
      pageSize = page.items.length;
    }
    return { plans: planList.items, exercises: catalog.items, sessions, next };
  }

  clear() {
    this.client.clear();
  }
}
