<script lang="ts">
	import { api } from '$lib/api/client';
	import { deviceState } from '$lib/stores/device';
	import { showToast } from '$lib/stores/ui';
	import { formatErrorMessage, logger } from '$lib/utils';
	import type { Pset } from '$lib/types';
	import {
		PsetSelector,
		SingleTighteningForm,
		AutoTighteningPanel,
		MultiSpindleConfig,
		FailureInjectionPanel,
		OperationModeControl,
		TighteningCurveMonitor
	} from '$lib/components/control';
	import { onMount } from 'svelte';
	import ControlTabs from '$lib/components/ui/ControlTabs.svelte';
	import DataCard from '$lib/components/ui/DataCard.svelte';
	import { JobRuntimePanel } from '$lib/components/jobs';
	import { refreshDeviceState } from '$lib/stores/websocket';

	let psets: Pset[] = $state([]);
	let activeTab = $state('tightening');
	let isLoadingPsets = $state(false);
	let psetLoadError: Error | null = $state(null);

	const currentPset = $derived(psets.find((p) => p.id === $deviceState?.current_pset_id));

	const tabs = [
		{ id: 'tightening', label: '拧紧控制', icon: '⚙️' },
		{ id: 'automation', label: '自动化与多轴', icon: '🤖' },
		{ id: 'advanced', label: '故障注入与高级', icon: '🔧' }
	];

	async function loadPsets() {
		isLoadingPsets = true;
		psetLoadError = null;
		try {
			psets = await api.getPsets();
		} catch (error) {
			psetLoadError = error instanceof Error ? error : new Error(String(error));
			logger.error('Failed to load PSETs:', error);
			showToast({ type: 'error', message: formatErrorMessage('加载参数集失败', error) });
		} finally {
			isLoadingPsets = false;
		}
	}

	function handleTabChange(tabId: string) {
		activeTab = tabId;
	}

	async function restartJob(id: number) {
		try {
			await api.restartJob(id);
			await refreshDeviceState();
			showToast({ type: 'success', message: '作业已重启' });
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

	onMount(() => {
		loadPsets();
	});
</script>

<svelte:head>
	<title>控制中心 - 设备模拟器</title>
</svelte:head>

<div class="space-y-6 animate-fade-in">
	<!-- Header -->
	<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h1 class="text-3xl font-semibold text-surface-900 dark:text-surface-100">控制中心</h1>
			<p class="text-sm text-surface-600 dark:text-surface-400 mt-1">
				配置拧紧参数、触发模拟操作与自动化设置
			</p>
		</div>
		{#if currentPset}
			<div class="glass rounded-lg px-4 py-2">
				<div class="text-xs text-surface-600 dark:text-surface-400">当前生效 PSET</div>
				<div class="text-sm font-semibold text-surface-900 dark:text-surface-100 mt-0.5">
					{currentPset.name}
				</div>
			</div>
		{/if}
	</div>

	<OperationModeControl />

	{#if $deviceState?.current_job_status != null}
		<JobRuntimePanel onRestart={restartJob} onClear={clearJob} />
	{/if}

	<!-- Tabbed Interface -->
	<div class="card p-0 overflow-hidden">
		<ControlTabs {tabs} bind:activeTab onChange={handleTabChange} className="px-6 pt-6" />

		<div class="p-6">
			<!-- Tightening Tab -->
			{#if activeTab === 'tightening'}
				<div class="space-y-6 animate-slide-up">
					<div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
						<div class="lg:col-span-1">
							{#if isLoadingPsets}
								<div class="card p-6 text-center">
									<div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
									<p class="text-sm text-surface-600 dark:text-surface-400 mt-3">正在加载参数集...</p>
								</div>
							{:else if psetLoadError}
								<div class="card p-6 border-error-500 bg-error-50 dark:bg-error-900/20">
									<div class="space-y-4">
										<div class="flex items-center gap-2 text-error-700 dark:text-error-300">
											<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
												<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
											</svg>
											<span class="font-semibold">加载参数集失败</span>
										</div>
										<p class="text-sm text-surface-700 dark:text-surface-300">{psetLoadError.message}</p>
										<button class="btn variant-filled-primary w-full" onclick={loadPsets}>
											重试
										</button>
									</div>
								</div>
							{:else}
								<PsetSelector {psets} />
							{/if}
						</div>
						<div class="lg:col-span-2">
							<SingleTighteningForm {currentPset} />
						</div>
					</div>

					<!-- 实时拧紧曲线监控器 -->
					<TighteningCurveMonitor />
				</div>
			{/if}

			<!-- Automation Tab -->
			{#if activeTab === 'automation'}
				<div class="space-y-6 animate-slide-up">
					<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
						<AutoTighteningPanel />
						<MultiSpindleConfig />
					</div>

					<!-- 实时拧紧曲线监控器 -->
					<TighteningCurveMonitor />
				</div>
			{/if}

			<!-- Advanced Tab -->
			{#if activeTab === 'advanced'}
				<div class="animate-slide-up">
					<FailureInjectionPanel />
				</div>
			{/if}
		</div>
	</div>

	<!-- Quick Tips -->
	<DataCard
		title="💡 使用技巧"
		subtitle="优化您的测试流程"
		padding="md"
		className="glass"
	>
		<div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
			<div class="space-y-1">
				<div class="font-medium text-surface-900 dark:text-surface-100">参数集 (PSET) 联动</div>
				<p class="text-surface-600 dark:text-surface-400">
					切换参数集可直接使用预设的合格扭矩/角度上下限范围
				</p>
			</div>
			<div class="space-y-1">
				<div class="font-medium text-surface-900 dark:text-surface-100">自动循环拧紧</div>
				<p class="text-surface-600 dark:text-surface-400">
					支持按固定频率或随机间隔自动产生拧紧数据，模拟产线连续生产
				</p>
			</div>
			<div class="space-y-1">
				<div class="font-medium text-surface-900 dark:text-surface-100">异常注入模拟</div>
				<p class="text-surface-600 dark:text-surface-400">
					支持模拟网络延迟、随机丢包与断开重连，检验工控上位机容错
				</p>
			</div>
		</div>
	</DataCard>
</div>
