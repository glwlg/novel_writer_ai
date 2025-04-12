// src/store/volume.js
import {defineStore} from 'pinia';
import {volumeAPI} from '@/services/volumeAPI'; // Adjust path
import {generationAPI} from "@/services/generationAPI.js";
import {useSceneStore} from "@/store/scene.js";
import {useChapterStore} from "@/store/chapter.js"; // To fetch chapters for a volume

export const useVolumeStore = defineStore('volume', {
    state: () => ({
        volumes: [], // List for the current project, potentially enriched with minimal chapters
        activeVolume: null,
        isLoading: false,
        isGenerating: false,
        error: null,
        // activeVolume: null, // Optional: If needed for focus
    }),
    actions: {
        _setLoading(value) {
            this.isLoading = value;
        },
        _setError(error) {
            this.error = error ? (error.response?.data?.detail || error.message) : null;
        },
        clearVolumes() {
            this.volumes = [];
            this.error = null;
            this.isLoading = false;
        },
        async fetchVolumes(projectId) {
            if (!projectId) {
                this.clearVolumes();
                return;
            }
            this._setLoading(true);
            this._setError(null);
            try {
                const response = await volumeAPI.getVolumesByProject(projectId);
                // API returns VolumeRead which includes chapters. If not, fetch them separately.
                // Assuming API returns VolumeRead with chapters array
                this.volumes = response.data;
                const chapterStore = useChapterStore();
                const sceneStore = useSceneStore();
                await chapterStore.loadChaptersFromVolume(this.volumes);
                await sceneStore.loadScenesFromChapter(chapterStore.chapters);
            } catch (err) {
                this._setError(err);
                this.volumes = [];
            } finally {
                this._setLoading(false);
            }
        },
        async createVolume(projectId, volumeData) {
            this._setError(null);
            const payload = {...volumeData, project_id: projectId};
            try {
                const response = await volumeAPI.createVolume(projectId, payload);
                // API might return VolumeRead with empty chapters array initially
                this.volumes.push(response.data);
                // You might need to re-sort if order matters immediately
                this.volumes.sort((a, b) => a.order - b.order);
                return response.data;
            } catch (err) {
                this._setError(err);
                throw err;
            }
        },
        async updateVolume(volumeId, volumeUpdateData) {
            this._setError(null);
            try {
                const response = await volumeAPI.updateVolume(volumeId, volumeUpdateData);
                const index = this.volumes.findIndex(ch => ch.id === volumeId);
                if (index !== -1) {
                    // Preserve chapters if the update response doesn't include them
                    const existingChapters = this.volumes[index].chapters;
                    this.volumes[index] = {...response.data, chapters: response.data.chapters ?? existingChapters};
                }
                // Re-sort if order was changed
                if (volumeUpdateData.order !== undefined) {
                    this.volumes.sort((a, b) => a.order - b.order);
                }
                return response.data;
            } catch (err) {
                this._setError(err);
                throw err;
            }
        },
        async deleteVolume(volumeId) {
            this._setError(null);
            try {
                const response = await volumeAPI.deleteVolume(volumeId);
                this.volumes = this.volumes.filter(ch => ch.id !== volumeId);
                return response.data;
            } catch (err) {
                this._setError(err);
                throw err;
            }
        },
        // removeSceneFromVolume(volumeId, chapterId, sceneId) {
        //     const volume = this.volumes.find(v => v.id === volumeId);
        //
        // }
        // --- Generation ---
        async generateVolumeChapters(volumeId) {
            if (!volumeId) return;
            this._setLoading('generating', true);
            this._setError('generating', null);
            try {
                const response = await generationAPI.generateVolumeChapters(volumeId);
                const updatedVolume = response.data; // API returns the updated chapter

                // Update the active chapter state if it's the one being generated
                if (this.activeVolume?.id === volumeId) {
                    // Merge carefully, especially if generation only returns partial data
                    // Assuming it returns the full ChapterRead schema:
                    this.activeVolume = updatedVolume;
                }

                return updatedVolume;
            } catch (err) {
                this._setError('generating', err);
                // Potentially update chapter status to 'generation_failed' if desired
                // if (this.activeChapter?.id === chapterId) {
                //    this.activeChapter.status = 'generation_failed'; // Assuming ChapterStatus enum/type allows this
                // }
                throw err; // Re-throw for component feedback
            } finally {
                this._setLoading('generating', false);
            }
        },
    },
});