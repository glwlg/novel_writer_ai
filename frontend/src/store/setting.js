// src/store/setting.js
import {defineStore} from 'pinia';
import {settingAPI} from '@/services/settingAPI'; // Adjust path

export const useSettingStore = defineStore('setting', {
    state: () => ({
        settings: [], // List of settings for the current project
        isLoading: false,
        error: null,
    }),
    actions: {
        _setLoading(value) {
            this.isLoading = value;
        },
        _setError(error) {
            this.error = error ? (error.response?.data?.detail || error.message) : null;
        },
        clearSettings() {
            this.settings = [];
            this.error = null;
            this.isLoading = false;
        },
        async fetchSettings(projectId) {
            if (!projectId) {
                this.clearSettings();
                return;
            }
            this._setLoading(true);
            this._setError(null);
            try {
                const response = await settingAPI.getSettingsByProject(projectId);
                this.settings = response.data;
            } catch (err) {
                this._setError(err);
                this.settings = [];
            } finally {
                this._setLoading(false);
            }
        },
        async createSetting(projectId, settingData) {
            this._setError(null);
            const payload = {...settingData, project_id: projectId};
            try {
                const response = await settingAPI.createSetting(projectId, payload);
                this.settings.push(response.data);
                return response.data;
            } catch (err) {
                this._setError(err);
                throw err;
            }
        },
        async updateSetting(settingId, settingUpdateData) {
            this._setError(null);
            try {
                const response = await settingAPI.updateSetting(settingId, settingUpdateData);
                const index = this.settings.findIndex(s => s.id === settingId);
                if (index !== -1) {
                    this.settings[index] = response.data;
                }
                return response.data;
            } catch (err) {
                this._setError(err);
                throw err;
            }
        },
        async deleteSetting(settingId) {
            this._setError(null);
            try {
                const response = await settingAPI.deleteSetting(settingId);
                this.settings = this.settings.filter(s => s.id !== settingId);
                return response.data;
            } catch (err) {
                this._setError(err);
                throw err;
            }
        },
    },
});