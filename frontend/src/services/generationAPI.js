import apiClient from './apiClient';

class GenerationAPI {

    /**
     * 触发指定场景的 RAG 内容生成
     * @param {number} sceneId - 场景 ID
     * @returns {Promise<object>} - 更新后的场景信息 (符合 SceneRead schema)
     */
    generateSceneRAG = async (sceneId) => {
        return apiClient.post(`/scenes/${sceneId}/generate_rag`);
    };
}

const generationAPI = new GenerationAPI();
export {generationAPI};