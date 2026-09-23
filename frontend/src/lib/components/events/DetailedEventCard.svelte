<script lang="ts">
	import type { SimulatorEvent } from '$lib/types';
	import { Badge } from '../ui';
	import { formatTorque, formatAngle, formatBatchCounter } from '$lib/utils';

	interface Props {
		event: SimulatorEvent;
		index: number;
	}

	let { event, index }: Props = $props();
</script>

<article
	class="border-b border-surface-200-700-token px-5 py-4 even:bg-surface-100-800-token last:border-b-0"
>
	<header class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
		<div class="flex items-center gap-3">
			<Badge variant="filled-primary">{event.type}</Badge>
			<span class="text-xs uppercase tracking-wide text-surface-600-300-token"
				>Event #{index + 1}</span
			>
		</div>
	</header>

	{#if event.type === 'TighteningCompleted'}
		<dl class="mt-3 grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
			<div>
				<dt class="text-xs uppercase tracking-wide text-surface-600-300-token">判定结果</dt>
				<dd class="mt-1">
					<Badge
						variant={event.result.tightening_status ? 'filled-success' : 'filled-error'}
					>
						{event.result.tightening_status ? 'OK' : 'NOK'}
					</Badge>
				</dd>
			</div>
			<div>
				<dt class="text-xs uppercase tracking-wide text-surface-600-300-token">扭矩</dt>
				<dd class="mt-1 font-semibold">{formatTorque(event.result.torque)}</dd>
			</div>
			<div>
				<dt class="text-xs uppercase tracking-wide text-surface-600-300-token">角度</dt>
				<dd class="mt-1 font-semibold">{formatAngle(event.result.angle)}</dd>
			</div>
			<div>
				<dt class="text-xs uppercase tracking-wide text-surface-600-300-token">批次进度</dt>
				<dd class="mt-1 font-semibold">
					{formatBatchCounter(event.result.batch_counter, event.result.batch_size)}
				</dd>
			</div>
		</dl>
	{:else if event.type === 'MultiSpindleResultCompleted'}
		<dl class="mt-3 grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
			<div>
				<dt class="text-xs uppercase tracking-wide text-surface-600-300-token">判定结果</dt>
				<dd class="mt-1">
					<Badge
						variant={event.result.overall_status === 0 ? 'filled-success' : 'filled-error'}
					>
						{event.result.overall_status === 0 ? 'OK' : 'NOK'}
					</Badge>
				</dd>
			</div>
			<div>
				<dt class="text-xs uppercase tracking-wide text-surface-600-300-token">同步轴数</dt>
				<dd class="mt-1 font-semibold">{event.result.spindle_count}</dd>
			</div>
			<div>
				<dt class="text-xs uppercase tracking-wide text-surface-600-300-token">同步组 ID</dt>
				<dd class="mt-1 font-semibold">{event.result.sync_id}</dd>
			</div>
			<div>
				<dt class="text-xs uppercase tracking-wide text-surface-600-300-token">结果 ID</dt>
				<dd class="mt-1 font-semibold">{event.result.result_id}</dd>
			</div>
		</dl>
	{:else if event.type === 'BatchCompleted'}
		<p class="mt-3 text-sm text-surface-600-300-token">批次完成，累计总数: {event.total}</p>
	{:else if event.type === 'ToolStateChanged'}
		<p class="mt-3 text-sm text-surface-600-300-token">
			工具状态变更为: {event.enabled ? '使能 (Enabled)' : '禁用 (Disabled)'}
		</p>
	{:else if event.type === 'OperationModeChanged'}
		<p class="mt-3 text-sm text-surface-600-300-token">
			运行模式已切换为: {event.mode.toUpperCase()}
		</p>
	{:else if event.type === 'PsetChanged'}
		<p class="mt-3 text-sm text-surface-600-300-token">
			参数集切换为: {event.pset_name} (编号 {event.pset_id})
		</p>
	{:else if event.type === 'VehicleIdChanged'}
		<p class="mt-3 text-sm text-surface-600-300-token">车辆 VIN 已更新为: {event.vin}</p>
	{:else if event.type === 'MultiSpindleStatusCompleted'}
		<p class="mt-3 text-sm text-surface-600-300-token">
			状态: {event.status.status === 0
				? '等待中'
				: event.status.status === 1
					? '运行中'
					: '已完成'}
			· 同步组 ID {event.status.sync_id} · 轴数 {event.status.spindle_count}
		</p>
	{:else if event.type === 'AutoTighteningProgress'}
		<p class="mt-3 text-sm text-surface-600-300-token">
			自动循环 {event.running ? '运行中' : '已停止'} · {formatBatchCounter(
				event.counter,
				event.target_size
			)}
		</p>
	{:else if event.type === 'JobSelected' ||
		event.type === 'JobProgress' ||
		event.type === 'JobRestarted' ||
		event.type === 'JobCompleted' ||
		event.type === 'JobStepChanged'}
		<dl class="mt-3 grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
			<div>
				<dt class="text-xs uppercase opacity-60">作业名称</dt>
				<dd class="font-semibold">{event.state.job_name}</dd>
			</div>
			<div>
				<dt class="text-xs uppercase opacity-60">状态</dt>
				<dd class="font-semibold">{event.state.status.toUpperCase()}</dd>
			</div>
			<div>
				<dt class="text-xs uppercase opacity-60">步骤</dt>
				<dd class="font-semibold">{event.state.current_step} / {event.state.total_steps}</dd>
			</div>
			<div>
				<dt class="text-xs uppercase opacity-60">进度</dt>
				<dd class="font-semibold">{event.state.total_progress} / {event.state.total_batch_size}</dd>
			</div>
		</dl>
	{/if}
</article>
