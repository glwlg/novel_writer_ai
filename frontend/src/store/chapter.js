// src/store/chapter.js
import {defineStore} from 'pinia';
import {chapterAPI} from '@/services/chapterAPI'; // Adjust path
import {generationAPI} from "@/services/generationAPI.js";

export const useChapterStore = defineStore('chapter', {
    state: () => ({
        chapters: [], // List for the current project, potentially enriched with minimal scenes
        activeChapter: null,
        isLoading: false,
        isGenerating: false,
        error: null,
        // activeChapter: null, // Optional: If needed for focus
    }),
    actions: {
        _setLoading(type, value) {
            if (type === 'fatch') this.isLoading = value;
            if (type === 'generating') this.isGenerating = value;
        },
        _setError(type, error) {
            const message = error ? (error.response?.data?.detail || error.message) : null;
            if (type === 'fatch') this.error = message;
            if (type === 'generating') this.generationError = message;
        },
        clearChapters() {
            this.chapters = [];
            this.error = null;
            this.isLoading = false;
        },
        setActiveChapter(chapterId) {
            const chapter = this.chapters.find(ch => ch.id === chapterId);
            this.activeChapter = chapter || null;
        },
        clearActiveChapter() {
            this.activeChapter = null;
        },
        loadChaptersFromVolume(volumes) {
            this.chapters = []
            for (const volume of volumes) {
                for (const chapter of volume.chapters) {
                    this.chapters.push({...chapter, volume_id: volume.id});
                }
            }
        },
        async fetchChapters(projectId) {
            if (!projectId) {
                this.clearChapters();
                return;
            }
            this._setLoading('fatch', true);
            this._setError('fatch', null);
            try {
                const response = await chapterAPI.getChaptersByProject(projectId);
                this.chapters = response.data;
            } catch (err) {
                this._setError('fatch', err);
                this.chapters = [];
            } finally {
                this._setLoading('fatch', false);
            }
        },
        async fetchChaptersByVolumeId(volumeId) {
            if (!volumeId) {
                this.clearChapters();
                return;
            }
            this._setLoading('fatch', true);
            this._setError('fatch', null);
            try {
                const response = await chapterAPI.getChaptersByProject(volumeId);
                this.chapters = response.data;
            } catch (err) {
                this._setError('fatch', err);
                this.chapters = [];
            } finally {
                this._setLoading('fatch', false);
            }
        },
        async createChapter(projectId, volumeId, chapterData) {
            this._setError('fatch', null);
            const payload = {...chapterData, project_id: projectId};
            try {
                const response = await chapterAPI.createChapter(projectId, volumeId, payload);
                // API might return ChapterRead with empty scenes array initially
                this.chapters.push(response.data);
                // You might need to re-sort if order matters immediately
                this.chapters.sort((a, b) => a.order - b.order);
                return response.data;
            } catch (err) {
                this._setError('fatch', err);
                throw err;
            }
        },
        async updateChapter(chapterId, chapterUpdateData) {
            this._setError('fatch', null);
            try {
                const response = await chapterAPI.updateChapter(chapterId, chapterUpdateData);
                const index = this.chapters.findIndex(ch => ch.id === chapterId);
                if (index !== -1) {
                    // Preserve scenes if the update response doesn't include them
                    const existingScenes = this.chapters[index].scenes;
                    this.chapters[index] = {...response.data, scenes: response.data.scenes ?? existingScenes};
                }
                // Re-sort if order was changed
                if (chapterUpdateData.order !== undefined) {
                    this.chapters.sort((a, b) => a.order - b.order);
                }
                return response.data;
            } catch (err) {
                this._setError('fatch', err);
                throw err;
            }
        },
        async deleteChapter(chapterId) {
            this._setError('fatch', null);
            try {
                const response = await chapterAPI.deleteChapter(chapterId);
                this.chapters = this.chapters.filter(ch => ch.id !== chapterId);
                return response.data;
            } catch (err) {
                this._setError('fatch', err);
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
                // const volumeStore = useVolumeStore();
                // volumeStore.removeSceneFromVolume(chapter.volume_id, sceneId);
            }
        },
        // --- Generation ---
        async generateChapterScenes(chapterId) {
            if (!chapterId) return;
            this._setLoading('generating', true);
            this._setError('generating', null);
            try {
                const response = await generationAPI.generateChapterScenes(chapterId);
                const updatedChapter = response.data; // API returns the updated scene

                // Update the active scene state if it's the one being generated
                if (this.activeChapter?.id === chapterId) {
                    // Merge carefully, especially if generation only returns partial data
                    // Assuming it returns the full SceneRead schema:
                    this.activeChapter = updatedChapter;
                }

                return updatedChapter;
            } catch (err) {
                this._setError('generating', err);
                // Potentially update scene status to 'generation_failed' if desired
                // if (this.activeScene?.id === sceneId) {
                //    this.activeScene.status = 'generation_failed'; // Assuming SceneStatus enum/type allows this
                // }
                throw err; // Re-throw for component feedback
            } finally {
                this._setLoading('generating', false);
            }
        },
        // --- Generation ---
        async generateChapterContent(chapterId) {
            if (!chapterId) return;
            this._setLoading('generating', true);
            this._setError('generating', null);
            try {
                const response = await generationAPI.generateChapterContent(chapterId);
                const updatedChapter = response.data; // API returns the updated scene

                // Update the active scene state if it's the one being generated
                if (this.activeChapter?.id === chapterId) {
                    // Merge carefully, especially if generation only returns partial data
                    // Assuming it returns the full SceneRead schema:
                    this.activeChapter = updatedChapter;
                }

                return updatedChapter;
            } catch (err) {
                this._setError('generating', err);
                // Potentially update scene status to 'generation_failed' if desired
                // if (this.activeScene?.id === sceneId) {
                //    this.activeScene.status = 'generation_failed'; // Assuming SceneStatus enum/type allows this
                // }
                throw err; // Re-throw for component feedback
            } finally {
                this._setLoading('generating', false);
            }
        }
    },
});