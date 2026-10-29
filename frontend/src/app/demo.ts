import type {
  Category,
  CategoryDefaults,
  Exercise,
  Guidance,
  NextTraining,
  Plan,
  TrainingSession,
  Transport,
  User,
  WorkSet,
} from '../shared/types';
import { ApiError } from '../shared/api';
import { today } from '../shared/ui';
import { timestampResponse } from '../shared/response-time';

/** Explicit, isolated preview. Never used as a fallback for failed API calls. */
export class DemoTransport implements Transport {
  private user: User = {
    id: 'preview',
    unit: 'kg',
    rounding_step: '2.5',
    effort_scale: 'rpe',
    timezone: 'Europe/Berlin',
  };
  private exercises: Exercise[] = [
    'Kniebeuge',
    'Bankdrücken',
    'Langhantelrudern',
    'Beinpresse',
    'Seitheben',
    'Kreuzheben',
  ].map((name, i) => ({
    id: `exercise-${i}`,
    name,
    category: (['squat', 'bench_press', 'back', 'legs', 'shoulders', 'deadlift'] as Category[])[i],
    main: [0, 1, 5].includes(i),
    archived: false,
  }));
  private categoryDefaults: CategoryDefaults[] = Object.entries({
    squat: [240, 3, 7, 7.5],
    bench_press: [180, 4, 8, 8],
    deadlift: [240, 3, 6, 7],
    overhead_press: [150, 3, 10, 8.5],
    back: [120, 3, 12, 8.5],
    chest: [120, 3, 12, 8.5],
    shoulders: [90, 3, 12, 8.5],
    legs: [120, 3, 12, 8.5],
    biceps: [90, 3, 12, 8.5],
    triceps: [90, 3, 12, 8.5],
  }).map(([category, [rest_seconds, sets, reps, target]]) => ({
    category: category as Category,
    rest_seconds,
    sets,
    reps,
    target_rpe: String(target),
    target_effort: String(target),
  }));
  private defaultsFor(category: Category) {
    const value = this.categoryDefaults.find((d) => d.category === category)!;
    return {
      ...value,
      target_effort:
        this.user.effort_scale === 'rpe' ? value.target_rpe : String(10 - Number(value.target_rpe)),
    };
  }
  private plan: Plan = {
    id: 'preview-plan',
    title: 'Kraftaufbau · Block 01',
    start_date: today(),
    weeks: 6,
    status: 'active',
    recommendations: true,
    revision: 1,
    days: [0, 2, 4].map((weekday, i) => ({
      id: `day-${i}`,
      name: ['Ganzkörper A', 'Ganzkörper B', 'Ganzkörper C'][i],
      weekday,
      slots: this.exercises.slice(0, 5).map((e, j) => ({
        id: `slot-${i}-${j}`,
        exercise_id: e.id,
        exercise_name: e.name,
        category: e.category,
        main: e.main,
        rest_seconds: j < 2 ? 180 : 90,
        prescriptions: Array.from({ length: 6 }, (_, w) => ({
          week: w + 1,
          sets: 3,
          reps: j < 2 ? 5 : 10,
          target_rpe: '8',
          target_effort: '8',
          note: j === 0 ? 'Kontrolliert absenken. Jede Wiederholung zählt.' : '',
        })),
      })),
    })),
  };
  private sessions: TrainingSession[] = [];
  private plans: Plan[] = [this.plan];
  private shares = new Map<string, Plan>();
  constructor(options: { seedHistory?: boolean } = {}) {
    if (!options.seedHistory) return;
    const start = new Date();
    start.setDate(start.getDate() - 21);
    this.plan.start_date = start.toLocaleDateString('sv-SE');
    for (const [i, title] of ['Hypertrophie · Block 02', 'Grundlagen · 4 Wochen'].entries()) {
      const plan = this.duplicate(this.plan, title, today());
      plan.status = i === 0 ? 'draft' : 'archived';
      if (i === 1) {
        plan.weeks = 4;
        plan.days.forEach((d) =>
          d.slots.forEach((s) => {
            s.prescriptions = s.prescriptions.filter((p) => p.week <= 4);
          }),
        );
      }
      this.plans.push(plan);
    }
    for (let i = 6; i >= 1; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i * 3);
      date.setHours(17, 30, 0, 0);
      const day = this.plan.days[(6 - i) % 3];
      const session: TrainingSession = {
        id: `preview-history-${i}`,
        plan_id: this.plan.id,
        plan_title: this.plan.title,
        day_id: day.id,
        day_name: day.name,
        week: Math.floor((6 - i) / 3) + 1,
        unit: 'kg',
        effort_scale: 'rpe',
        started_at: date.toISOString(),
        ended_at: new Date(date.getTime() + 3900000).toISOString(),
        duration_seconds: 3900,
        server_now: new Date().toISOString(),
        rest_ends_at: null,
        rest_remaining_seconds: 0,
        slots: day.slots.map((slot, j) => ({
          ...structuredClone(slot),
          prescription: structuredClone(slot.prescriptions[Math.floor((6 - i) / 3)]),
          skipped: false,
          sets: Array.from({ length: 3 }, (_, n) => ({
            id: crypto.randomUUID(),
            weight: String([110, 75, 65, 160, 12.5][j] + (6 - i) * 2.5),
            reps: slot.prescriptions[0].reps,
            rpe: '8',
            effort: '8',
            e1rm: String([137.5, 95, 92.5, 225, 20][j] + (6 - i) * 2.5),
            recorded_at: new Date(date.getTime() + (j * 3 + n) * 180000).toISOString(),
          })),
        })),
      };
      this.sessions.unshift(session);
    }
    const more: [string, Category][] = [
      ['Frontkniebeuge', 'squat'],
      ['Pausenkniebeuge', 'squat'],
      ['Schrägbankdrücken', 'bench_press'],
      ['Kurzhantel-Bankdrücken', 'bench_press'],
      ['Rumänisches Kreuzheben', 'deadlift'],
      ['Überkopfdrücken', 'overhead_press'],
      ['Klimmzüge', 'back'],
      ['Latzug', 'back'],
      ['Butterfly', 'chest'],
      ['Kabel-Flys', 'chest'],
      ['Reverse Flys', 'shoulders'],
      ['Face Pulls', 'shoulders'],
      ['Beinstrecker', 'legs'],
      ['Beinbeuger', 'legs'],
      ['Wadenheben', 'legs'],
      ['Langhantelcurls', 'biceps'],
      ['Hammercurls', 'biceps'],
      ['Trizepsdrücken', 'triceps'],
      ['French Press', 'triceps'],
    ];
    this.exercises.push(
      ...more.map(([name, category], i) => ({
        id: `extra-exercise-${i}`,
        name,
        category,
        main: category === 'overhead_press',
        archived: false,
      })),
    );
  }
  private duplicate(source: Plan, title: string, start: string): Plan {
    const copy = structuredClone(source);
    copy.id = crypto.randomUUID();
    copy.title = title;
    copy.start_date = start;
    copy.status = 'draft';
    copy.revision = 1;
    copy.days.forEach((d) => {
      d.id = crypto.randomUUID();
      d.slots.forEach((s) => {
        s.id = crypto.randomUUID();
      });
    });
    return copy;
  }
  async request<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
    const value = await this.route(path, method, body as Record<string, unknown> | undefined);
    return timestampResponse(structuredClone(value)) as T;
  }
  private snapshot(session: TrainingSession) {
    return {
      ...session,
      server_now: new Date().toISOString(),
      rest_remaining_seconds: session.rest_ends_at
        ? Math.max(0, Math.ceil((Date.parse(session.rest_ends_at) - Date.now()) / 1000))
        : 0,
    };
  }
  private async route(
    path: string,
    method: string,
    body?: Record<string, unknown>,
  ): Promise<unknown> {
    if (
      !path.startsWith('/training-sessions') &&
      path !== '/auth/me' &&
      path !== '/plans/next-training'
    )
      return this.manage(path, method, body ?? {});
    if (path === '/auth/me') return this.user;
    if (path === '/plans') return { items: this.plans };
    if (path === '/exercises') return { items: this.exercises };
    if (path === '/plans/next-training') {
      const active = this.plans.find((p) => p.status === 'active');
      let nextDay: string | null = null,
        nextWeek: number | null = null;
      if (active)
        for (let week = 1; week <= active.weeks && !nextDay; week++) {
          const day = active.days.find(
            (d) =>
              !this.sessions.some(
                (s) =>
                  s.plan_id === active.id && s.day_id === d.id && s.week === week && s.ended_at,
              ),
          );
          if (day) {
            nextDay = day.id;
            nextWeek = week;
          }
        }
      return {
        plan_id: this.plans.find((p) => p.status === 'active')?.id ?? null,
        day_id: nextDay,
        week: nextWeek,
        scheduled_date: today(),
        running_training_session_id: this.sessions.find((s) => !s.ended_at)?.id ?? null,
      } satisfies NextTraining;
    }
    if (path.startsWith('/training-sessions?'))
      return {
        items: this.sessions
          .slice(
            Number(new URL(path, 'http://preview.local').searchParams.get('offset') ?? 0),
            Number(new URL(path, 'http://preview.local').searchParams.get('offset') ?? 0) +
              Number(new URL(path, 'http://preview.local').searchParams.get('limit') ?? 50),
          )
          .map((s) => this.snapshot(s)),
      };
    if (path === '/training-sessions' && method === 'POST') {
      if (this.sessions.some((s) => !s.ended_at))
        throw new ApiError(409, 'Ein Training läuft bereits. Öffne es über die Übersicht.');
      const plan = this.plans.find((p) => p.id === body?.plan_id);
      if (!plan) throw new ApiError(404, 'Plan nicht gefunden.');
      const day = plan.days.find((d) => d.id === body?.day_id)!;
      const session: TrainingSession = {
        id: crypto.randomUUID(),
        plan_id: plan.id,
        plan_title: plan.title,
        day_id: day.id,
        day_name: day.name,
        week: Number(body?.week),
        unit: this.user.unit,
        effort_scale: this.user.effort_scale,
        slots: day.slots.map((s) => ({
          ...s,
          prescription: s.prescriptions[Number(body?.week) - 1],
          skipped: false,
          sets: [],
        })),
        started_at: new Date().toISOString(),
        ended_at: null,
        duration_seconds: null,
        server_now: new Date().toISOString(),
        rest_ends_at: null,
        rest_remaining_seconds: 0,
      };
      this.sessions.unshift(session);
      return session;
    }
    const parts = path.split('/').filter(Boolean);
    if (parts[0] === 'training-sessions') {
      const session = this.sessions.find((s) => s.id === parts[1]);
      if (!session) throw new ApiError(404, 'Training nicht gefunden.');
      if (parts.length === 2) return this.snapshot(session);
      if (parts[2] === 'times') {
        session.started_at = String(body?.started_at);
        session.ended_at = body?.ended_at ? String(body.ended_at) : null;
        session.duration_seconds = session.ended_at
          ? (Date.parse(session.ended_at) - Date.parse(session.started_at)) / 1000
          : null;
        return this.snapshot(session);
      }
      if (parts[2] === 'finish') {
        session.ended_at = new Date().toISOString();
        session.duration_seconds = Math.floor((Date.now() - Date.parse(session.started_at)) / 1000);
        session.rest_ends_at = null;
        return this.snapshot(session);
      }
      if (parts[2] === 'timer') {
        session.rest_ends_at =
          body?.delta_seconds == null
            ? null
            : new Date(
                Math.max(
                  Date.now(),
                  Date.parse(session.rest_ends_at || new Date().toISOString()) +
                    Number(body.delta_seconds) * 1000,
                ),
              ).toISOString();
        return this.snapshot(session);
      }
      const slot = session.slots.find((s) => s.id === parts[3])!;
      if (parts[4] === 'guidance') {
        const previous = this.sessions
          .filter((s) => s.id !== session.id && s.started_at < session.started_at)
          .flatMap((s) =>
            s.slots.filter(
              (s) => s.id === slot.id && s.prescription.reps === slot.prescription.reps,
            ),
          )
          .find((s) => s.sets.length);
        return {
          unit: this.user.unit,
          recommended_weight: this.plans.find((p) => p.id === session.plan_id)?.recommendations
            ? (previous?.sets[0]?.weight ?? null)
            : null,
          backoff_weight: null,
          last_sets: previous?.sets ?? [],
          last_performed_at: previous?.sets.at(-1)?.recorded_at ?? null,
        } satisfies Guidance;
      }
      if (parts[4] === 'skipped') {
        slot.skipped = Boolean(body?.skipped);
        return this.snapshot(session);
      }
      if (parts[4] === 'sets') {
        if (method === 'DELETE') {
          slot.sets = slot.sets.filter((s) => s.id !== parts[5]);
          return this.snapshot(session);
        }
        const weight = Number(body?.weight),
          reps = Number(body?.reps),
          effort = Number(body?.effort);
        const rpe = this.user.effort_scale === 'rpe' ? effort : 10 - effort;
        const step = Number(this.user.rounding_step);
        const e1rm = Math.ceil((weight * (1 + (reps + 10 - rpe) / 30)) / step) * step;
        const set: WorkSet = {
          id: parts[5] || crypto.randomUUID(),
          weight: String(weight),
          reps,
          effort: String(effort),
          rpe: String(rpe),
          e1rm: String(e1rm),
          recorded_at:
            slot.sets.find((s) => s.id === parts[5])?.recorded_at ?? new Date().toISOString(),
        };
        slot.sets = parts[5]
          ? slot.sets.map((s) => (s.id === parts[5] ? set : s))
          : [...slot.sets, set];
        if (!session.ended_at)
          session.rest_ends_at = new Date(Date.now() + slot.rest_seconds * 1000).toISOString();
        return {
          training_session: this.snapshot(session),
          work_set: set,
          backoff_weight: String(
            Math.round(
              e1rm /
                (1 + (slot.prescription.reps + 10 - Number(slot.prescription.target_rpe)) / 30) /
                step,
            ) * step,
          ),
          new_personal_record: false,
        };
      }
    }
    throw new ApiError(
      400,
      'Die Vorschau zeigt den Trainingsablauf. Melde dich an, um deine eigenen Pläne und Daten zu speichern.',
    );
  }
  private async manage(
    path: string,
    method: string,
    body: Record<string, unknown>,
  ): Promise<unknown> {
    const parts = path.split('/').filter(Boolean);
    if (path === '/auth/logout') return undefined;
    if (path === '/users/me/preferences') {
      const old = this.user;
      this.user = { ...this.user, ...body } as User;
      const factor =
        old.unit === this.user.unit ? 1 : this.user.unit === 'lb' ? 2.2046226218 : 1 / 2.2046226218;
      const convert = (v: string) => String(Number((Number(v) * factor).toFixed(4)));
      this.plans.forEach((p) =>
        p.days.forEach((d) =>
          d.slots.forEach((s) =>
            s.prescriptions.forEach((r) => {
              r.target_effort =
                this.user.effort_scale === 'rpe' ? r.target_rpe : String(10 - Number(r.target_rpe));
            }),
          ),
        ),
      );
      this.sessions.forEach((s) => {
        s.unit = this.user.unit;
        s.effort_scale = this.user.effort_scale;
        s.slots.forEach((slot) => {
          slot.prescription.target_effort =
            this.user.effort_scale === 'rpe'
              ? slot.prescription.target_rpe
              : String(10 - Number(slot.prescription.target_rpe));
          slot.sets.forEach((set) => {
            set.weight = convert(set.weight);
            set.e1rm = convert(set.e1rm);
            set.effort = this.user.effort_scale === 'rpe' ? set.rpe : String(10 - Number(set.rpe));
          });
        });
      });
      return this.user;
    }
    if (path === '/users/me/export')
      return {
        format_version: 3,
        user: this.user,
        exercises: this.exercises,
        category_defaults: this.categoryDefaults.map((d) => this.defaultsFor(d.category)),
        plans: this.plans,
        training_sessions: this.sessions.map((s) => this.snapshot(s)),
        identities: [],
        login_email: null,
        shared_templates: [...this.shares.values()],
      };
    if (path === '/users/me' && method === 'DELETE') {
      this.plans = [];
      this.sessions = [];
      this.exercises = [];
      return undefined;
    }
    if (parts[0] === 'exercises' && parts[1] === 'category-defaults') {
      if (method === 'GET')
        return { items: this.categoryDefaults.map((d) => this.defaultsFor(d.category)) };
      const category = parts[2] as Category;
      const target_rpe =
        this.user.effort_scale === 'rpe'
          ? String(body.target_effort)
          : String(10 - Number(body.target_effort));
      this.categoryDefaults = this.categoryDefaults.map((d) =>
        d.category === category
          ? {
              ...d,
              rest_seconds: Number(body.rest_seconds),
              sets: Number(body.sets),
              reps: Number(body.reps),
              target_rpe,
            }
          : d,
      );
      return this.defaultsFor(category);
    }
    if (parts[0] === 'exercises') {
      if (parts.length === 1 && method === 'GET') return { items: this.exercises };
      if (parts.length === 1 && method === 'POST') {
        const exercise: Exercise = {
          id: crypto.randomUUID(),
          name: String(body.name),
          category: body.category as Category,
          main: Boolean(body.main),
          archived: false,
        };
        this.exercises.push(exercise);
        return exercise;
      }
      const exercise = this.exercises.find((e) => e.id === parts[1]);
      if (!exercise) throw new ApiError(404, 'Übung nicht gefunden.');
      if (method === 'DELETE') {
        exercise.archived = true;
        return undefined;
      }
      Object.assign(exercise, body);
      this.plans.forEach((plan) =>
        plan.days.forEach((day) =>
          day.slots.forEach((slot) => {
            if (slot.exercise_id === exercise.id)
              Object.assign(slot, {
                exercise_name: exercise.name,
                category: exercise.category,
                main: exercise.main,
              });
          }),
        ),
      );
      return exercise;
    }
    if (parts[0] === 'templates') {
      if (method === 'DELETE') {
        this.shares.delete(parts[1]);
        return undefined;
      }
      const original = this.shares.get(parts[1]);
      if (!original) throw new ApiError(404, 'Vorlage nicht gefunden.');
      const plan = this.duplicate(original, String(body.title), String(body.start_date));
      this.plans.push(plan);
      return plan;
    }
    if (parts[0] === 'plans') {
      if (parts.length === 1) {
        if (method === 'GET') return { items: this.plans };
        const plan: Plan = {
          id: crypto.randomUUID(),
          title: String(body.title),
          start_date: String(body.start_date),
          weeks: Number(body.weeks),
          status: 'draft',
          revision: 1,
          recommendations: true,
          days: (body.days as { name: string; weekday: number }[]).map((d) => ({
            ...d,
            id: crypto.randomUUID(),
            slots: [],
          })),
        };
        this.plans.push(plan);
        return plan;
      }
      const plan = this.plans.find((p) => p.id === parts[1]);
      if (!plan) throw new ApiError(404, 'Plan nicht gefunden.');
      if (parts.length === 2) {
        if (method === 'DELETE') {
          this.plans = this.plans.filter((p) => p.id !== plan.id);
          return undefined;
        }
        if (method === 'PUT') {
          Object.assign(plan, body);
          plan.revision++;
        }
        return plan;
      }
      if (parts[2] === 'duplicate') {
        const copy = this.duplicate(plan, String(body.title), String(body.start_date));
        this.plans.push(copy);
        return copy;
      }
      if (parts[2] === 'shares') {
        const token = crypto.randomUUID();
        this.shares.set(token, structuredClone(plan));
        return { token };
      }
      if (parts[2] === 'status') {
        if (body.status === 'active')
          this.plans
            .filter((p) => p.status === 'active')
            .forEach((p) => {
              p.status = 'ended';
            });
        plan.status = body.status as Plan['status'];
      }
      if (parts[2] === 'days') {
        const day = plan.days.find((d) => d.id === parts[3]);
        if (!day) throw new ApiError(404, 'Trainingstag nicht gefunden.');
        if (parts.length === 4) {
          day.name = String(body.name);
          day.weekday = Number(body.weekday);
        } else if (parts[4] === 'slot-order') {
          const order = body.slot_ids as string[];
          day.slots.sort((a, b) => order.indexOf(a.id) - order.indexOf(b.id));
        } else if (parts.length === 5) {
          const e = this.exercises.find((e) => e.id === body.exercise_id);
          if (!e) throw new ApiError(404, 'Übung nicht gefunden.');
          day.slots.push({
            id: crypto.randomUUID(),
            exercise_id: e.id,
            exercise_name: e.name,
            category: e.category,
            main: e.main,
            rest_seconds: Number(body.rest_seconds ?? this.defaultsFor(e.category).rest_seconds),
            prescriptions: Array.from({ length: plan.weeks }, (_, i) => ({
              week: i + 1,
              sets: this.defaultsFor(e.category).sets,
              reps: this.defaultsFor(e.category).reps,
              target_rpe: this.defaultsFor(e.category).target_rpe,
              target_effort: this.defaultsFor(e.category).target_effort,
              note: '',
            })),
          });
        } else if (method === 'DELETE') day.slots = day.slots.filter((s) => s.id !== parts[5]);
        else {
          const slot = day.slots.find((s) => s.id === parts[5]);
          if (slot) slot.rest_seconds = Number(body.rest_seconds);
        }
      }
      if (parts[2] === 'slots') {
        const slot = plan.days.flatMap((d) => d.slots).find((s) => s.id === parts[3]);
        if (!slot) throw new ApiError(404, 'Übungsslot nicht gefunden.');
        const week = Number(parts[5]);
        const effort = String(body.target_effort);
        slot.prescriptions = [
          ...slot.prescriptions.filter((p) => p.week !== week),
          {
            week,
            sets: Number(body.sets),
            reps: Number(body.reps),
            target_effort: effort,
            target_rpe: this.user.effort_scale === 'rpe' ? effort : String(10 - Number(effort)),
            note: String(body.note ?? ''),
          },
        ].sort((a, b) => a.week - b.week);
      }
      if (parts[2] === 'weeks') {
        const week = Number(parts[3]);
        plan.days.forEach((d) =>
          d.slots.forEach((s) => {
            const rx = s.prescriptions.find((p) => p.week === week);
            if (rx)
              for (let w = week + 1; w <= plan.weeks; w++)
                s.prescriptions = [
                  ...s.prescriptions.filter((p) => p.week !== w),
                  { ...rx, week: w },
                ];
          }),
        );
      }
      if (parts[2] === 'progression') {
        if (parts[3] === 'apply' && Number(body.expected_revision) !== plan.revision)
          throw new ApiError(409, 'Der Plan wurde geändert. Erstelle eine neue Vorschau.');
        const result = structuredClone(plan);
        result.days.forEach((d) =>
          d.slots.forEach((s) => {
            const first = s.prescriptions.find((p) => p.week === 1);
            if (!first) throw new ApiError(409, 'Ergänze zuerst Woche 1.');
            s.prescriptions = Array.from({ length: plan.weeks }, (_, i) => {
              const deload = Boolean(body.deload) && i === plan.weeks - 1 && i > 0;
              const rpe = String(
                deload
                  ? s.main
                    ? 6
                    : 7
                  : Math.min(
                      s.main ? 9 : 10,
                      Number(first.target_rpe) + i * Number(body.increment ?? 0.5),
                    ),
              );
              return {
                ...first,
                week: i + 1,
                sets: deload ? Math.max(1, first.sets - 1) : first.sets,
                target_rpe: rpe,
                target_effort: this.user.effort_scale === 'rpe' ? rpe : String(10 - Number(rpe)),
              };
            });
          }),
        );
        if (parts[3] === 'preview') return { base_revision: plan.revision, plan: result };
        plan.days = result.days;
      }
      plan.revision++;
      return plan;
    }
    throw new ApiError(404, 'Diese Vorschau-Seite wurde nicht gefunden.');
  }
}
