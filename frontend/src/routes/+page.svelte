<script lang="ts">
	import { deviceState } from '$lib/stores/device';
	import {
		latestTighteningResult,
		tighteningStats,
		torqueSparkline,
		angleSparkline,
		successRateSparkline
	} from '$lib/stores/tightening';
	import { events } from '$lib/stores/events';
	import { connectionHealth, latency, packetLoss } from '$lib/stores/websocket';
	import { api } from '$lib/api/client';
	import { showToast } from '$lib/stores/ui';
	import { Badge } from '$lib/components/ui';
	import { EventTimeline } from '$lib/components/events';
	import { formatPercentage, formatErrorMessage } from '$lib/utils';
	import DataCard from '$lib/components/ui/DataCard.svelte';
	import MetricSparkline from '$lib/components/ui/MetricSparkline.svelte';
	import HealthMonitor from '$lib/components/ui/HealthMonitor.svelte';
	import StatusIndicator from '$lib/components/ui/StatusIndicator.svelte';
	import { refreshDeviceState } from '$lib/stores/websocket';

	let isSimulating = $state(false);
	const isToolEnabled = $derived($deviceState?.tool_enabled ?? true);
	const isCompletedJob = $derived(
		$deviceState?.current_job_status === 'ok' || $deviceState?.current_job_status === 'nok'
	);

	async function handleSimulateTightening() {
		if (!isToolEnabled) {
			showToast({
				type: 'warning',
				message: 'Tool is disabled. Enable the tool before simulating tightening.'
			});
			return;
		}

		isSimulating = true;
		try {
			await api.simulateTightening();
			await refreshDeviceState();
			showToast({ type: 'success', message: 'Tightening simulated!' });
		} catch (error) {
			showToast({ type: 'error', message: formatErrorMessage('simulate tightening', error) });
		} finally {
			isSimulating = false;
		}
	}
</script>

<svelte:head>
	<title>仪表盘 - Open Protocol 设备模拟器</title>
</svelte:head>

<div class="space-y-8 animate-fade-in">
	<!-- Header with Quick Action -->
	<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h1 class="text-3xl font-semibold text-surface-900 dark:text-surface-100">
				总控仪表盘
			</h1>
			<p class="text-sm text-surface-600 dark:text-surface-400 mt-1">
				实时运行总览与系统监控状态
			</p>
		</div>
		<button
			class="btn variant-filled-primary {isSimulating ? 'loading' : ''}"
			onclick={handleSimulateTightening}
			disabled={isSimulating || !isToolEnabled || isCompletedJob}
			title={isCompletedJob
				? '重启或退出已完成的作业'
				: isToolEnabled
					? '模拟单次拧紧'
					: '工具已被禁用'}
		>
			{isSimulating ? '正在模拟...' : '⚡ 快速模拟拧紧'}
		</button>
	</div>

	<!-- Hero Section - 3-column layout -->
	<div class="grid grid-cols-1 lg:grid-cols-3 gap-6 stagger-children">
		<!-- Device Status -->
		<DataCard title="设备运行状态" subtitle="实时配置与连接" hover={true}>
			{#if $deviceState}
				<div class="space-y-4">
					<dl class="space-y-3">
						<div class="flex items-center justify-between">
							<dt class="text-xs uppercase tracking-wide text-surface-600 dark:text-surface-400">
								单元编号 (Cell ID)
							</dt>
							<dd class="font-semibold text-surface-900 dark:text-surface-100">
								{$deviceState.cell_id}
							</dd>
						</div>
						<div class="divider-fade"></div>
						<div class="flex items-center justify-between">
							<dt class="text-xs uppercase tracking-wide text-surface-600 dark:text-surface-400">
								当前作业 (Active Job)
							</dt>
							<dd class="text-right">
								{#if $deviceState.current_job_status}
									<div class="flex items-center justify-end gap-2">
										<Badge
											variant={$deviceState.current_job_status === 'running'
												? 'filled-primary'
												: $deviceState.current_job_status === 'ok'
													? 'filled-success'
													: 'filled-error'}
										>
											{$deviceState.current_job_name}
										</Badge>
										<span class="text-xs text-surface-500">
											{$deviceState.current_job_status.toUpperCase()}
										</span>
									</div>
									<p class="mt-1 text-xs opacity-60">
										步骤 {$deviceState.current_job_step} / {$deviceState.current_job_total_steps}
										· {$deviceState.current_job_total_progress} /
										{$deviceState.current_job_total_batch_size}
									</p>
								{:else}
									<Badge variant="soft">无</Badge>
								{/if}
							</dd>
						</div>
						<div class="divider-fade"></div>
						<div class="flex items-center justify-between">
							<dt class="text-xs uppercase tracking-wide text-surface-600 dark:text-surface-400">
								通道编号 (Channel ID)
							</dt>
							<dd class="font-semibold text-surface-900 dark:text-surface-100">
								{$deviceState.channel_id}
							</dd>
						</div>

						<div class="divider-fade"></div>
						<div class="flex items-center justify-between">
							<dt class="text-xs uppercase tracking-wide text-surface-600 dark:text-surface-400">
								工具使能状态
							</dt>
							<dd>
								<StatusIndicator
									status={$deviceState.tool_enabled ? 'success' : 'warning'}
									label={$deviceState.tool_state === 'Enabled' ? '已使能' : '已禁用'}
									size="sm"
									showLabel={true}
								/>
							</dd>
						</div>
						<div class="divider-fade"></div>
						<div class="flex items-center justify-between">
							<dt class="text-xs uppercase tracking-wide text-surface-600 dark:text-surface-400">
								生效参数集 (PSET)
							</dt>
							<dd class="flex items-center gap-2">
								{#if $deviceState.current_pset_name}
									<Badge variant="filled-primary">
										{$deviceState.current_pset_name}
									</Badge>
									<span class="text-xs text-surface-500">
										(编号 {$deviceState.current_pset_id})
									</span>
								{:else}
									<Badge variant="soft">无</Badge>
								{/if}
							</dd>
						</div>
						<div class="divider-fade"></div>
						<div class="flex items-center justify-between">
							<dt class="text-xs uppercase tracking-wide text-surface-600 dark:text-surface-400">
								多轴同步拧紧
							</dt>
							<dd class="flex items-center gap-2">
								<Badge
									variant={$deviceState.multi_spindle_config.enabled ? 'filled-primary' : 'soft'}
								>
									{$deviceState.multi_spindle_config.enabled ? '已启用' : '未启用'}
								</Badge>
								{#if $deviceState.multi_spindle_config.enabled}
									<span class="text-xs text-surface-500">
										({$deviceState.multi_spindle_config.spindle_count} 轴)
									</span>
								{/if}
							</dd>
						</div>
					</dl>
				</div>
			{:else}
				<div class="flex items-center justify-center py-8 opacity-70">
					<div class="loading-skeleton" style="width: 100%; height: 120px;"></div>
				</div>
			{/if}
		</DataCard>

		<!-- Latest Tightening -->
		<DataCard title="最新拧紧数据" subtitle="最近一次拧紧循环" hover={true} accent={true}>
			{#if $latestTighteningResult}
				<div class="space-y-4">
					<div class="flex items-center justify-between">
						<span class="text-sm text-surface-600 dark:text-surface-400">判定结果</span>
						<StatusIndicator
							status={$latestTighteningResult.tightening_status ? 'success' : 'error'}
							label={$latestTighteningResult.tightening_status ? '合格 (OK)' : '超差 (NOK)'}
							size="md"
						/>
					</div>
					<div class="grid grid-cols-2 gap-4 pt-2">
						<div>
							<div class="text-3xl font-semibold text-surface-900 dark:text-surface-100">
								{$latestTighteningResult.torque.toFixed(2)}
							</div>
							<div class="text-xs text-surface-500 dark:text-surface-400 mt-1">
								扭矩 (N·m)
							</div>
						</div>
						<div>
							<div class="text-3xl font-semibold text-surface-900 dark:text-surface-100">
								{$latestTighteningResult.angle.toFixed(1)}
							</div>
							<div class="text-xs text-surface-500 dark:text-surface-400 mt-1">
								角度 (°)
							</div>
						</div>
					</div>
					<div class="divider-fade"></div>
					<div class="space-y-2">
						<div class="flex items-center justify-between text-sm">
							<span class="text-surface-600 dark:text-surface-400">批次完成进度</span>
							<span class="font-semibold text-surface-900 dark:text-surface-100">
								{$latestTighteningResult.batch_counter} / {$latestTighteningResult.batch_size}
							</span>
						</div>
						<div class="w-full bg-surface-200 dark:bg-surface-700 rounded-full h-2 overflow-hidden">
							<div
								class="bg-primary-500 h-full transition-all duration-300 ease-out"
								style="width: {($latestTighteningResult.batch_counter / $latestTighteningResult.batch_size) * 100}%"
							></div>
						</div>
						<div class="text-xs text-center text-surface-500 dark:text-surface-400">
							已完成 {Math.round(($latestTighteningResult.batch_counter / $latestTighteningResult.batch_size) * 100)}%
						</div>
					</div>
				</div>
			{:else}
				<div class="rounded-lg border-2 border-dashed border-surface-300 dark:border-surface-400 p-8 text-center">
					<p class="text-sm text-surface-500 dark:text-surface-400">
						暂无拧紧结果数据
					</p>
				</div>
			{/if}
		</DataCard>

		<!-- Connection Health Monitor -->
		<DataCard title="通信健康状态" subtitle="网络延迟与丢包指标" hover={true}>

			<HealthMonitor
				connectionHealth={$connectionHealth}
				packetLoss={$packetLoss}
				latency={$latency}
			/>
		</DataCard>
	</div>

	<!-- Performance Metrics with Sparklines -->
	<DataCard padding="lg">
		{#snippet headerAction()}
			<div class="flex items-center gap-2">
				<span class="text-2xs uppercase tracking-wide text-surface-500 dark:text-surface-400">
					实时指标监控
				</span>
				<div class="h-2 w-2 rounded-full bg-success-500 animate-pulse"></div>
			</div>
		{/snippet}

		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
			<div class="metric-card card p-5 space-y-3">
				<div class="flex items-center justify-between">
					<span class="text-sm text-surface-600 dark:text-surface-400">累计拧紧循环</span>
					<span class="text-2xl">🔄</span>
				</div>
				<div class="text-3xl font-semibold text-surface-900 dark:text-surface-100">
					{$tighteningStats.total}
				</div>
			</div>

			<div class="metric-card card p-5">
				<MetricSparkline
					label="合格率"
					value={formatPercentage($tighteningStats.successRate)}
					trend={$tighteningStats.successRate >= 90 ? 'up' : $tighteningStats.successRate < 70 ? 'down' : 'neutral'}
					trendData={$successRateSparkline}
					color="rgb(var(--color-success-500))"
					icon="✓"
				/>
			</div>

			<div class="metric-card card p-5">
				<MetricSparkline
					label="平均扭矩"
					value={$tighteningStats.avgTorque.toFixed(2)}
					unit="N·m"
					trend="neutral"
					trendData={$torqueSparkline}
					color="rgb(var(--color-primary-500))"
					icon="⚙️"
				/>
			</div>

			<div class="metric-card card p-5">
				<MetricSparkline
					label="平均角度"
					value={$tighteningStats.avgAngle.toFixed(1)}
					unit="°"
					trend="neutral"
					trendData={$angleSparkline}
					color="rgb(var(--color-tertiary-500))"
					icon="↻"
				/>
			</div>
		</div>
	</DataCard>

	<!-- Recent Events Timeline -->
	<DataCard title="最近事件流" subtitle="模拟器最新 5 条事件记录">
		{#snippet headerAction()}
			<a href="/events" class="btn variant-ghost-surface btn-sm">
				查看全部 →
			</a>
		{/snippet}

		{#if $events.length > 0}
			<EventTimeline events={$events} limit={5} showNumbers={true} />
		{:else}
			<div class="py-12">
				<div class="text-center text-surface-500 dark:text-surface-400">
					<p class="text-sm">暂无事件记录</p>
					<p class="text-xs mt-1">触发拧紧循环后事件将显示在此处</p>
				</div>
			</div>
		{/if}
	</DataCard>

	<!-- Quick Navigation Footer -->
	<div class="glass rounded-xl p-6">
		<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
			<div>
				<h3 class="text-lg font-medium text-surface-900 dark:text-surface-100">
					快捷操作与配置
				</h3>
				<p class="text-sm text-surface-600 dark:text-surface-400 mt-1">
					直接进入高级参数设置或控制中心
				</p>
			</div>
			<div class="flex flex-wrap gap-3">
				<a href="/control" class="btn variant-filled-primary">
					控制中心
				</a>
				<a href="/psets" class="btn variant-ghost-surface">
					参数集 (PSET)
				</a>
				<a href="/jobs" class="btn variant-ghost-surface">
					作业管理 (Job)
				</a>
				<a href="/events" class="btn variant-ghost-surface">
					事件日志
				</a>
			</div>
		</div>
	</div>
</div>
