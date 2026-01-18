import { configureStore } from '@reduxjs/toolkit'

// Reducers (後で追加)
// import sitesReducer from './slices/sitesSlice'
// import vehiclesReducer from './slices/vehiclesSlice'

export const store = configureStore({
  reducer: {
    // sites: sitesReducer,
    // vehicles: vehiclesReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
