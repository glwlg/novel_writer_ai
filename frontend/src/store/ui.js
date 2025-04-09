// src/store/ui.js
import { defineStore } from 'pinia';

export const useUIStore = defineStore('ui', {
  state: () => ({
    isLoadingGlobal: false, // For app-wide loading states if needed
    globalError: null,      // For displaying global error messages/banners
    activeModal: null,      // Tracks which modal might be open (e.g., 'projectForm', 'characterForm')
  }),
  actions: {
    setLoading(isLoading) {
      this.isLoadingGlobal = isLoading;
    },
    setError(errorMessage) {
      this.globalError = errorMessage;
      // Optional: Set a timer to clear the error after a few seconds
      // setTimeout(() => { this.clearError(); }, 5000);
    },
    clearError() {
      this.globalError = null;
    },
    openModal(modalName) {
      this.activeModal = modalName;
    },
    closeModal() {
      this.activeModal = null;
    }
  },
});