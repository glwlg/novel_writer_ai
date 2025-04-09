// src/store/relationship.js
import { defineStore } from 'pinia';
import {relationshipAPI} from '@/services/relationshipAPI'; // Adjust path
import { useCharacterStore } from './character'; // To get character names for display

export const useRelationshipStore = defineStore('relationship', {
  state: () => ({
    relationships: [], // List for the current project
    isLoading: false,
    error: null,
  }),
  getters: {
    // Example getter to enrich relationship data with character names
    relationshipsWithNames: (state) => {
      const characterStore = useCharacterStore();
      return state.relationships.map(rel => {
        const char1 = characterStore.characters.find(c => c.id === rel.character1_id);
        const char2 = characterStore.characters.find(c => c.id === rel.character2_id);
        return {
          ...rel,
          character1_name: char1?.name || `ID: ${rel.character1_id}`,
          character2_name: char2?.name || `ID: ${rel.character2_id}`,
        };
      });
    },
  },
  actions: {
    _setLoading(value) { this.isLoading = value; },
    _setError(error) { this.error = error ? (error.response?.data?.detail || error.message) : null; },
    clearRelationships() {
        this.relationships = [];
        this.error = null;
        this.isLoading = false;
    },
    async fetchRelationships(projectId, characterId = null) { // Allow filtering by character
        if (!projectId) {
            this.clearRelationships();
            return;
        }
      this._setLoading(true);
      this._setError(null);
      try {
        // API service needs to handle the optional characterId parameter
        const response = await relationshipAPI.getRelationshipsByProject(projectId, characterId);
        this.relationships = response.data;
      } catch (err) {
        this._setError(err);
        this.relationships = [];
      } finally {
        this._setLoading(false);
      }
    },
    async createRelationship(projectId, relationshipData) {
       this._setError(null);
       const payload = { ...relationshipData, project_id: projectId };
      try {
        const response = await relationshipAPI.createRelationship(projectId, payload);
        this.relationships.push(response.data);
        return response.data;
      } catch (err) {
        this._setError(err);
        throw err;
      }
    },
    async updateRelationship(relationshipId, relationshipUpdateData) {
        this._setError(null);
      try {
        const response = await relationshipAPI.updateRelationship(relationshipId, relationshipUpdateData);
        const index = this.relationships.findIndex(r => r.id === relationshipId);
        if (index !== -1) {
          this.relationships[index] = response.data;
        }
        return response.data;
      } catch (err) {
        this._setError(err);
        throw err;
      }
    },
    async deleteRelationship(relationshipId) {
       this._setError(null);
      try {
       const response =  await relationshipAPI.deleteRelationship(relationshipId);
        this.relationships = this.relationships.filter(r => r.id !== relationshipId);
        return response.data;
      } catch (err) {
        this._setError(err);
        throw err;
      }
    },
    // Helper action if needed after deleting a character
    // removeRelationshipsInvolvingCharacter(characterId) {
    //    this.relationships = this.relationships.filter(r => r.character1_id !== characterId && r.character2_id !== characterId);
    // }
  },
});