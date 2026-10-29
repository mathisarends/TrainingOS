import { createContext } from '@lit/context';
import type { App } from 'lit-canon-composition';
import type { Transport } from '../shared/types';
import type { TrainingStore } from './store';

export const transportContext = createContext<Transport>('trainingos.transport');
export const storeContext = createContext<TrainingStore>('trainingos.store');
export const navigationContext = createContext<Pick<App, 'navigate'>>('trainingos.navigation');
