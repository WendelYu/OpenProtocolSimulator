<script lang="ts">
	import { page } from '$app/state';

	const navItems = [
		{ href: '/', label: '仪表盘' },
		{ href: '/control', label: '控制中心' },
		{ href: '/psets', label: '参数集 (PSET)' },
		{ href: '/jobs', label: '作业管理 (Jobs)' },
		{ href: '/protocol', label: '协议配置' },
		{ href: '/events', label: '实时事件' }
	];

</script>

<nav class="flex gap-4">
	{#each navItems as item}
		<a
			href={item.href}
			class="btn btn-sm"
			class:variant-filled-primary={page.url.pathname === item.href}
			class:variant-ghost-surface={page.url.pathname !== item.href}
		>
			{item.label}
		</a>
	{/each}
</nav>
