// src/store/character.js
import {defineStore} from 'pinia';
import {characterAPI} from '@/services/characterAPI'; // Adjust path

export const useCharacterStore = defineStore('character', {
    state: () => ({
        characters: [], // List of characters for the current project
        isLoading: false,
        error: null,
        // currentCharacter: null, // Optional: if you have a dedicated character detail view state
    }),
    actions: {
        _setLoading(value) {
            this.isLoading = value;
        },
        _setError(error) {
            this.error = error ? (error.response?.data?.detail || error.message) : null;
        },
        clearCharacters() {
            this.characters = [];
            this.error = null;
            this.isLoading = false;
        },
        async fetchCharacters(projectId) {
            if (!projectId) {
                this.clearCharacters();
                return;
            }
            this._setLoading(true);
            this._setError(null);
            try {
                const response = await characterAPI.getCharactersByProject(projectId);
                this.characters = response.data;
            } catch (err) {
                this._setError(err);
                this.characters = []; // Clear on error
            } finally {
                this._setLoading(false);
            }
        },
        async createCharacter(projectId, characterData) {
            this._setError(null);
            // Pass the correct project ID in the payload
            const payload = {...characterData, project_id: projectId};
            try {
                const response = await characterAPI.createCharacter(projectId, payload);
                this.characters.push(response.data);
                return response.data;
            } catch (err) {
                this._setError(err);
                throw err;
            }
        },
        async updateCharacter(characterId, characterUpdateData) {
            this._setError(null);
            // Optional: Add specific loading state
            try {
                const response = await characterAPI.updateCharacter(characterId, characterUpdateData);
                const index = this.characters.findIndex(c => c.id === characterId);
                if (index !== -1) {
                    // Use spread operator carefully to merge, or replace entirely
                    this.characters[index] = response.data; // Assuming API returns the full updated object
                }
                return response.data;
            } catch (err) {
                this._setError(err);
                throw err;
            }
        },
        async deleteCharacter(characterId) {
            this._setError(null);
            // Optional: Add specific loading state
            try {
                const response = await characterAPI.deleteCharacter(characterId);
                this.characters = this.characters.filter(c => c.id !== characterId);
                // If relationships are managed here or need update, trigger that
                // const relationshipStore = useRelationshipStore();
                // relationshipStore.removeRelationshipsInvolvingCharacter(characterId);
                return response.data;
            } catch (err) {
                this._setError(err);
                throw err;
            }
        },
    },
});