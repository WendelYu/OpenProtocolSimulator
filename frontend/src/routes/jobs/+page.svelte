<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api/client';
	import { JobCard, JobModal, JobRuntimePanel } from '$lib/components/jobs';
	import { Button, EmptyState } from '$lib/components/ui';
	import { deviceState } from '$lib/stores/device';
	import { showToast } from '$lib/stores/ui';
	import { formatErrorMessage } from '$lib/utils';
	import { refreshDeviceState } from '$lib/stores/websocket';
	import type { Job, Pset } from '$lib/types';

	let jobs: Job[] = $state([]);
	let psets: Pset[] = $state([]);
	let loading = $state(true);
	let searchQuery = $state('');
	let modalOpen = $state(false);
	let modalMode: 'create' | 'edit' = $state('create');
	let editingJob: Job | null = $state(null);

	const running = $derived($deviceState?.current_job_status === 'running');
	const jobModeSelected = $derived($deviceState?.operation_mode === 'job');
	const filteredJobs = $derived.by(() => {
		const query = searchQuery.trim().toLowerCase();
		if (!query) return jobs;
		return jobs.filter(
			(job) =>
				job.name.toLowerCase().includes(query) ||
				job.id.toString().padStart(2, '0').includes(query) ||
				job.steps.some((step) => step.pset_id.toString().includes(query))
		);
	});

	async function loadData() {
		loading = true;
		try {
			[jobs, psets] = await Promise.all([api.getJobs(), api.getPsets()]);
		} catch (error) {
			showToast({ type: 'error', message: formatErrorMessage('加载作业失败', error) });
		} finally {
			loading = false;
		}
	}

	function openCreate() {
		modalMode = 'create';
		editingJob = null;
		modalOpen = true;
	}

	function openEdit(job: Job) {
		modalMode = 'edit';
		editingJob = job;
		modalOpen = true;
	}

	async function saveJob(job: Job) {
		try {
			if (modalMode === 'create') {
				await api.createJob(job);
				showToast({ type: 'success', message: `作业 ${job.id.toString().padStart(2, '0')} 创建成功` });
			} else {
				await api.updateJob(job.id, job);
				showToast({ type: 'success', message: `作业 ${job.id.toString().padStart(2, '0')} 更新成功` });
			}
			modalOpen = false;
			await loadData();
		} catch (error) {
			showToast({ type: 'error', message: formatErrorMessage('保存作业失败', error) });
			throw error;
		}
	}

	async function deleteJob(id: number) {
		if (!window.confirm(`确定要删除作业 ${id.toString().padStart(2, '0')} 吗？`)) return;
		try {
			await api.deleteJob(id);
			showToast({ type: 'success', message: '作业已成功删除' });
			await loadData();
		} catch (error) {
			showToast({ type: 'error', message: formatErrorMessage('删除作业失败', error) });
		}
	}

	async function selectJob(id: number) {
		if (!jobModeSelected) return;
		try {
			await api.selectJob(id);
			await refreshDeviceState();
			showToast({ type: 'success', message: `已选择作业 ${id.toString().padStart(2, '0')}` });
		} catch (error) {
			showToast({ type: 'error', message: formatErrorMessage('选择作业失败', error) });
		}
	}

	async function restartJob(id: number) {
		try {
			await api.restartJob(id);
			await refreshDeviceState();
			showToast({ type: 'success', message: `作业 ${id.toString().padStart(2, '0')} 已重新启动` });
		} catch (error) {
			showToast({ type: 'error', message: formatErrorMessage('重启作业失败', error) });
		}
	}

	async function clearJob() {
		try {
			await api.clearActiveJob();
			await refreshDeviceState();
			showToast({ type: 'success', message: '已退出作业模式' });
		} catch (error) {
			showToast({ type: 'error', message: formatErrorMessage('退出作业模式失败', error) });
		}
	}

	onMount(loadData);
</script>

<svelte:head>
	<title>作业管理 - 设备模拟器</title>
</svelte:head>

<div class="space-y-6 animate-fade-in">
	<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h1 class="text-3xl font-semibold">作业管理 (Job)</h1>
			<p class="mt-1 text-sm opacity-70">
				配置持久化作业步骤并控制作业模式 (JobMode) 运行状态。
			</p>
		</div>
		<Button onclick={openCreate} disabled={psets.length === 0}>+ 新增作业</Button>
	</div>

	<JobRuntimePanel onRestart={restartJob} onClear={clearJob} />

	{#if !jobModeSelected}
		<p class="rounded-md bg-warning-50 p-3 text-sm text-warning-700 dark:bg-warning-900/20">
			请先在控制中心切换为“作业 (Job)”运行模式，然后再启动作业。
		</p>
	{/if}

	{#if jobs.length > 0}
		<input
			class="input max-w-md"
			type="search"
			placeholder="搜索作业名称、编号或包含的参数集..."
			bind:value={searchQuery}
		/>
	{/if}

	{#if loading}
		<div class="card p-8 text-center">正在加载作业数据...</div>
	{:else if psets.length === 0}
		<EmptyState
			title="请先创建参数集"
			description="每个作业步骤都必须关联一个已存在的参数集 (PSET)。"
			icon="!"
		>
			{#snippet action()}
				<a class="btn variant-filled-primary" href="/psets">前往创建参数集</a>
			{/snippet}
		</EmptyState>
	{:else if jobs.length === 0}
		<EmptyState
			title="暂无配置的作业"
			description="作业可通过此页面或 REST API 配置，并通过 Open Protocol MID 0030-0033 进行数据交互。"
			icon="J"
		>
			{#snippet action()}
				<Button onclick={openCreate}>创建第一个作业</Button>
			{/snippet}
		</EmptyState>
	{:else if filteredJobs.length === 0}
		<EmptyState title="未匹配到作业" description="请修改或清空搜索关键词。" icon="?" />
	{:else}
		<div class="grid auto-rows-fr gap-5 md:grid-cols-2 xl:grid-cols-3">
			{#each filteredJobs as job (job.id)}
				<JobCard
					{job}
					active={$deviceState?.current_job_status != null &&
						$deviceState?.current_job_id === job.id}
					{running}
					selectionEnabled={jobModeSelected}
					onEdit={openEdit}
					onDelete={deleteJob}
					onSelect={selectJob}
				/>
			{/each}
		</div>
	{/if}
</div>

<JobModal
	open={modalOpen}
	mode={modalMode}
	job={editingJob}
	{psets}
	channelId={$deviceState?.channel_id ?? 1}
	onsubmit={saveJob}
	onclose={() => (modalOpen = false)}
/>
