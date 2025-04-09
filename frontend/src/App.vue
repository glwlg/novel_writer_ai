<template>
  <!-- App.vue 是最顶层的容器 -->
  <div id="app-container">
    <!--
      <router-view> 组件会根据当前 URL 渲染匹配到的路由组件。
      例如，访问 / 时渲染 ProjectDashboard.vue，
      访问 /projects/123/characters 时渲染 CharactersList.vue (嵌套在 ProjectWorkspace.vue 内)。
    -->
    <router-view v-slot="{ Component, route }">
      <!-- 可以添加过渡效果 -->
      <transition name="fade" mode="out-in">
        <component :is="Component" :key="route.path" />
      </transition>
    </router-view>

    <!-- 你可以在这里放置全局元素，比如全局通知组件，
         但通常导航栏、侧边栏等布局元素会放在具体的布局组件 (如 ProjectWorkspace.vue) 中 -->
    <!-- <GlobalNotificationComponent /> -->
  </div>
</template>

<script setup>
// 使用 <script setup> 语法 (Vue 3 推荐)
// 通常 App.vue 不需要太多逻辑，它只是一个渲染路由内容的容器。
// 全局状态的初始化可以在 Pinia stores 中完成。

// 可以在这里监听全局事件或执行一次性设置，但尽量保持简洁。
import { onMounted } from 'vue';

onMounted(() => {
  console.log('App component mounted');
  // 可以在此进行一些应用级别的初始化检查，比如检查 token
});

</script>

<style>
/* 这里可以放一些非常基础的全局样式，但更推荐放在 main.js 导入的 CSS 文件中 */

#app-container {
  min-height: 100vh; /* 确保应用容器至少占满整个视口高度 */
  display: flex;
  flex-direction: column;
}

/* 简单的淡入淡出过渡效果 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>