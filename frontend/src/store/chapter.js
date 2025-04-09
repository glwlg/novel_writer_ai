// src/store/chapter.js
import { defineStore } from 'pinia';
import {chapterAPI} from '@/services/chapterAPI'; // Adjust path
import {sceneAPI} from '@/services/sceneAPI'; // To fetch scenes for a chapter

export const useChapterStore = defineStore('chapter', {
  state: () => ({
    chapters: [], // List for the current project, potentially enriched with minimal scenes
    isLoading: false,
    error: null,
    // activeChapter: null, // Optional: If needed for focus
  }),
  actions: {
    _setLoading(value) { this.isLoading = value; },
    _setError(error) { this.error = error ? (error.response?.data?.detail || error.message) : null; },
    clearChapters() {
        this.chapters = [];
        this.error = null;
        this.isLoading = false;
    },
    async fetchChapters(projectId) {
        if (!projectId) {
            this.clearChapters();
            return;
        }
      this._setLoading(true);
      this._setError(null);
      try {
        const response = await chapterAPI.getChaptersByProject(projectId);
        // API returns ChapterRead which includes scenes. If not, fetch them separately.
        // Assuming API returns ChapterRead with scenes array
        this.chapters = response.data;

        // If API only returns chapter metadata, you'd loop and fetch scenes:
        // const chaptersData = response.data;
        // const chaptersWithScenes = await Promise.all(chaptersData.map(async (chap) => {
        //    try {
        //      const scenesResponse = await sceneAPI.getScenesByChapter(chap.id);
        //      return { ...chap, scenes: scenesResponse.data };
        //    } catch (sceneErr) {
        //      console.error(`Failed to fetch scenes for chapter ${chap.id}:`, sceneErr);
        //      return { ...chap, scenes: [] }; // Assign empty array on error
        //    }
        // }));
        // this.chapters = chaptersWithScenes;

      } catch (err) {
        this._setError(err);
        this.chapters = [];
      } finally {
        this._setLoading(false);
      }
    },
    async createChapter(projectId, chapterData) {
      this._setError(null);
      const payload = { ...chapterData, project_id: projectId };
      try {
        const response = await chapterAPI.createChapter(projectId, payload);
        // API might return ChapterRead with empty scenes array initially
        this.chapters.push(response.data);
        // You might need to re-sort if order matters immediately
        this.chapters.sort((a, b) => a.order - b.order);
        return response.data;
      } catch (err) {
        this._setError(err);
        throw err;
      }
    },
    async updateChapter(chapterId, chapterUpdateData) {
       this._setError(null);
      try {
        const response = await chapterAPI.updateChapter(chapterId, chapterUpdateData);
        const index = this.chapters.findIndex(ch => ch.id === chapterId);
        if (index !== -1) {
            // Preserve scenes if the update response doesn't include them
           const existingScenes = this.chapters[index].scenes;
           this.chapters[index] = { ...response.data, scenes: response.data.scenes ?? existingScenes };
        }
         // Re-sort if order was changed
        if (chapterUpdateData.order !== undefined) {
             this.chapters.sort((a, b) => a.order - b.order);
        }
        return response.data;
      } catch (err) {
        this._setError(err);
        throw err;
      }
    },
    async deleteChapter(chapterId) {
        this._setError(null);
      try {
        const response = await chapterAPI.deleteChapter(chapterId);
        this.chapters = this.chapters.filter(ch => ch.id !== chapterId);
        // Note: Associated scenes are deleted by backend cascade,
        // but if you manage scene state separately, ensure it's updated.
        // const sceneStore = useSceneStore();
        // sceneStore.removeScenesByChapter(chapterId); // Implement this in sceneStore if needed
          return response.data;
      } catch (err) {
        this._setError(err);
        throw err;
      }
    },
    // Action to potentially add a scene to a chapter's local state
    // (useful if creating a scene doesn't return the updated chapter)
    addSceneToChapter(chapterId, scene) {
        const chapter = this.chapters.find(ch => ch.id === chapterId);
        if (chapter) {
            if (!chapter.scenes) chapter.scenes = [];
            chapter.scenes.push(scene);
            // Sort scenes within the chapter if needed
            chapter.scenes.sort((a, b) => a.order_in_chapter - b.order_in_chapter);
        }
    },
    // Action to remove a scene from a chapter's local state
    removeSceneFromChapter(chapterId, sceneId) {
        const chapter = this.chapters.find(ch => ch.id === chapterId);
        if (chapter && chapter.scenes) {
             chapter.scenes = chapter.scenes.filter(s => s.id !== sceneId);
        }
    }
  },
});