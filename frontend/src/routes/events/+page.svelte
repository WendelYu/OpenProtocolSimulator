<script lang="ts">
	import {
		filteredEvents,
		eventFilter,
		eventSearchQuery,
		clearEvents,
		eventCounts
	} from '$lib/stores/events';
	import { Button, Badge } from '$lib/components/ui';
	import DetailedEventCard from '$lib/components/events/DetailedEventCard.svelte';
	import DataCard from '$lib/components/ui/DataCard.svelte';
	import ViewModeToggle from '$lib/components/ui/ViewModeToggle.svelte';
	import ChipFilter from '$lib/components/ui/ChipFilter.svelte';
	import EmptyState from '$lib/components/ui/EmptyState.svelte';
	import { formatTorque, formatAngle, formatBatchCounter } from '$lib/utils';

	let viewMode = $state('table');

	const eventTypes = [
		{ id: 'all', label: '所有事件', icon: '📋' },
		{ id: 'TighteningCompleted', label: '单次拧紧', icon: '⚙️' },
		{ id: 'MultiSpindleResultCompleted', label: '多轴结果', icon: '🔧' },
		{ id: 'BatchCompleted', label: '批次完成', icon: '📦' },
		{ id: 'ToolStateChanged', label: '工具状态', icon: '🔄' },
		{ id: 'OperationModeChanged', label: '模式切换', icon: '🎛️' },
		{ id: 'PsetChanged', label: '参数集切换', icon: '⚡' },
		{ id: 'VehicleIdChanged', label: '车辆 VIN', icon: '🚗' },
		{ id: 'AutoTighteningProgress', label: '自动循环进度', icon: '⏱️' },
		{ id: 'JobSelected', label: '作业已选', icon: 'J' },
		{ id: 'JobProgress', label: '作业进度', icon: 'J' },
		{ id: 'JobStepChanged', label: '作业步骤', icon: 'J' },
		{ id: 'JobRestarted', label: '作业重启', icon: 'J' },
		{ id: 'JobCompleted', label: '作业完成', icon: 'J' }
	];

	const viewModes = [
		{ id: 'table', label: '表格视图', icon: '📊' },
		{ id: 'detailed', label: '详细视图', icon: '📝' },
		{ id: 'compact', label: '紧凑视图', icon: '📋' }
	];

	function handleFilterToggle(filterId: string) {
		if (filterId === 'all') {
			$eventFilter = 'all';
		} else {
			$eventFilter = $eventFilter === filterId ? 'all' : filterId;
		}
	}

	function handleClearAll() {
		$eventFilter = 'all';
		$eventSearchQuery = '';
	}
</script>

<svelte:head>
	<title>事件日志 - 设备模拟器</title>
</svelte:head>

<div class="space-y-6 animate-fade-in">
	<!-- Header -->
	<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h1 class="text-3xl font-semibold text-surface-900 dark:text-surface-100">事件日志 (Event Log)</h1>
			<p class="text-sm text-surface-600 dark:text-surface-400 mt-1">
				实时模拟器事件流、动作历史与通信记录
			</p>
		</div>
		<div class="flex items-center gap-3">
			<ViewModeToggle modes={viewModes} bind:activeMode={viewMode} onChange={() => {}} />
			<Button variant="filled-error" onclick={clearEvents}>🗑️ 清空所有记录</Button>
		</div>
	</div>

	<!-- Filters & Search -->
	<DataCard padding="md">
		<div class="space-y-4">
			<!-- Search Bar -->
			<div class="relative">
				<svg
					class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-surface-400"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
					/>
				</svg>
				<input
					type="search"
					class="input !pl-11 w-full"
					placeholder="按内容、事件类型或参数搜索事件..."
					bind:value={$eventSearchQuery}
				/>
			</div>

			<!-- Filter Chips -->
			<div>
				<div class="flex items-center justify-between mb-3">
					<span class="text-sm font-medium text-surface-700 dark:text-surface-300">
						事件类别过滤
					</span>
					{#if $eventFilter !== 'all' || $eventSearchQuery}
						<button
							type="button"
							class="text-xs text-surface-600 dark:text-surface-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
							onclick={handleClearAll}
						>
							重置过滤器
						</button>
					{/if}
				</div>
				<div class="flex flex-wrap gap-2">
					{#each eventTypes as type}
						<ChipFilter
							label="{type.icon} {type.label}{type.id !== 'all' && $eventCounts[type.id]
								? ` (${$eventCounts[type.id]})`
								: ''}"
							value={type.id}
							active={$eventFilter === type.id}
							onClick={handleFilterToggle}
							removable={false}
							variant={$eventFilter === type.id ? 'primary' : 'default'}
						/>
					{/each}
				</div>
			</div>
		</div>
	</DataCard>

	<!-- Event List -->
	<div class="space-y-4">
		{#if $filteredEvents.length > 0}
			<!-- Event Count Header -->
			<div class="flex items-center justify-between">
				<p class="text-sm text-surface-600 dark:text-surface-400">
					当前显示 <span class="font-semibold text-surface-900 dark:text-surface-100"
						>{$filteredEvents.length}</span
					>
					条事件
				</p>
			</div>

			<!-- Events Container -->
			{#if viewMode === 'table'}
				<!-- Table View -->
				<div class="card overflow-hidden">
					<div class="overflow-x-auto">
						<table class="w-full">
							<thead class="bg-surface-100 dark:bg-surface-300 border-b border-surface-200 dark:border-surface-700">
								<tr>
									<th class="px-4 py-3 text-left text-xs font-semibold text-surface-400 dark:text-surface-300 uppercase tracking-wider">序号</th>
									<th class="px-4 py-3 text-left text-xs font-semibold text-surface-400 dark:text-surface-300 uppercase tracking-wider">事件类型</th>
									<th class="px-4 py-3 text-left text-xs font-semibold text-surface-400 dark:text-surface-300 uppercase tracking-wider">状态判定</th>
									<th class="px-4 py-3 text-left text-xs font-semibold text-surface-400 dark:text-surface-300 uppercase tracking-wider">详细数据</th>
								</tr>
							</thead>
							<tbody class="divide-y divide-surface-200 dark:divide-surface-700">
								{#each $filteredEvents as event, i}
									<tr class="hover:bg-surface-50 dark:hover:bg-surface-800/50 transition-colors animate-slide-up" style="animation-delay: {Math.min(i, 20) * 0.02}s">
										<td class="px-4 py-3 text-sm text-surface-600 dark:text-surface-400">{i + 1}</td>
										<td class="px-4 py-3">
											<Badge variant="filled-primary">{event.type}</Badge>
										</td>
										<td class="px-4 py-3">
											{#if event.type === 'TighteningCompleted'}
												<Badge variant={event.result.tightening_status ? 'filled-success' : 'filled-error'}>
													{event.result.tightening_status ? 'OK' : 'NOK'}
												</Badge>
											{:else if event.type === 'MultiSpindleResultCompleted'}
												<Badge variant={event.result.overall_status === 0 ? 'filled-success' : 'filled-error'}>
													{event.result.overall_status === 0 ? 'OK' : 'NOK'}
												</Badge>
											{:else if event.type === 'ToolStateChanged'}
												<Badge variant={event.enabled ? 'filled-success' : 'filled-error'}>
													{event.enabled ? 'Enabled' : 'Disabled'}
												</Badge>
											{:else if event.type === 'OperationModeChanged'}
												<Badge variant="filled-primary">{event.mode.toUpperCase()}</Badge>
												{:else if event.type === 'AutoTighteningProgress'}
													<Badge variant={event.running ? 'filled-primary' : 'soft'}>
														{event.running ? 'Running' : 'Stopped'}
													</Badge>
												{:else if event.type === 'JobSelected' ||
													event.type === 'JobProgress' ||
													event.type === 'JobStepChanged' ||
													event.type === 'JobRestarted' ||
													event.type === 'JobCompleted'}
													<Badge
														variant={event.state.status === 'running'
															? 'filled-primary'
															: event.state.status === 'ok'
																? 'filled-success'
																: 'filled-error'}
													>
														{event.state.status.toUpperCase()}
													</Badge>
												{:else}
												<span class="text-sm text-surface-500 dark:text-surface-400">—</span>
											{/if}
										</td>
										<td class="px-4 py-3">
											{#if event.type === 'TighteningCompleted'}
												<div class="flex gap-4 text-sm">
													<span><span class="text-surface-600 dark:text-surface-400">扭矩:</span> <span class="font-semibold">{formatTorque(event.result.torque)}</span></span>
													<span><span class="text-surface-600 dark:text-surface-400">角度:</span> <span class="font-semibold">{formatAngle(event.result.angle)}</span></span>
													<span><span class="text-surface-600 dark:text-surface-400">批次:</span> <span class="font-semibold">{formatBatchCounter(event.result.batch_counter, event.result.batch_size)}</span></span>
												</div>
											{:else if event.type === 'MultiSpindleResultCompleted'}
												<div class="flex gap-4 text-sm">
													<span><span class="text-surface-600 dark:text-surface-400">轴数:</span> <span class="font-semibold">{event.result.spindle_count}</span></span>
													<span><span class="text-surface-600 dark:text-surface-400">同步ID:</span> <span class="font-semibold">{event.result.sync_id}</span></span>
												</div>
											{:else if event.type === 'BatchCompleted'}
												<span class="text-sm"><span class="text-surface-600 dark:text-surface-400">累计总量:</span> <span class="font-semibold">{event.total}</span></span>
											{:else if event.type === 'PsetChanged'}
												<span class="text-sm"><span class="text-surface-600 dark:text-surface-400">参数集:</span> <span class="font-semibold">{event.pset_name} (编号 {event.pset_id})</span></span>
											{:else if event.type === 'VehicleIdChanged'}
												<span class="text-sm"><span class="text-surface-600 dark:text-surface-400">VIN:</span> <span class="font-semibold">{event.vin}</span></span>
											{:else if event.type === 'AutoTighteningProgress'}
												<span class="text-sm"><span class="text-surface-600 dark:text-surface-400">循环进度:</span> <span class="font-semibold">{formatBatchCounter(event.counter, event.target_size)}</span></span>
												{:else if event.type === 'MultiSpindleStatusCompleted'}
													<div class="flex gap-4 text-sm">
														<span><span class="text-surface-600 dark:text-surface-400">状态:</span> <span class="font-semibold">{event.status.status === 0 ? '等待中' : event.status.status === 1 ? '运行中' : '已完成'}</span></span>
														<span><span class="text-surface-600 dark:text-surface-400">同步ID:</span> <span class="font-semibold">{event.status.sync_id}</span></span>
													</div>
												{:else if event.type === 'JobSelected' ||
													event.type === 'JobProgress' ||
													event.type === 'JobStepChanged' ||
													event.type === 'JobRestarted' ||
													event.type === 'JobCompleted'}
													<span class="text-sm">
														<span class="font-semibold">{event.state.job_name}</span>
														· 步骤 {event.state.current_step}/{event.state.total_steps}
														· 批次 {event.state.total_progress}/{event.state.total_batch_size}
													</span>
												{/if}
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<div class="space-y-3">
					{#each $filteredEvents as event, i}
						{#if viewMode === 'detailed'}
							<div class="animate-slide-up" style="animation-delay: {Math.min(i, 20) * 0.02}s">
								<DetailedEventCard {event} index={i} />
							</div>
						{:else}
							<!-- Compact View -->
							<div
								class="card p-4 hover-lift flex items-center justify-between gap-4 animate-slide-up"
								style="animation-delay: {Math.min(i, 20) * 0.02}s"
							>
								<div class="flex items-center gap-3 flex-1 min-w-0">
									<div
										class="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center text-xs font-semibold text-primary-700 dark:text-primary-300"
									>
										{i + 1}
									</div>
									<div class="flex-1 min-w-0">
										<span
											class="font-medium text-surface-900 dark:text-surface-100 truncate"
										>
											{event.type}
										</span>
									</div>
								</div>
							</div>
						{/if}
					{/each}
				</div>
			{/if}
		{:else}
			<EmptyState
				title="未找到匹配事件"
				description={$eventSearchQuery
					? `没有与关键词 "${$eventSearchQuery}" 匹配的事件`
					: $eventFilter !== 'all'
						? `暂无类别为 "${$eventFilter}" 的事件`
						: '模拟器目前尚未记录任何事件'}
				icon="🔍"
			>
				{#snippet action()}
					{#if $eventFilter !== 'all' || $eventSearchQuery}
						<button class="btn variant-filled-primary" onclick={handleClearAll}>
							清除过滤条件
						</button>
					{:else}
						<a href="/control" class="btn variant-filled-primary">
							前往模拟拧紧
						</a>
					{/if}
				{/snippet}
			</EmptyState>
		{/if}
	</div>
</div>
