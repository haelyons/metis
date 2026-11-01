    function validateProfile() {
      facts.profile_complete = false
      facts.timed_fraction = null
      facts.gpu_telemetry = null
      rmSync(path.join(A, 'profile-packet.json'), { force: true })
      try {
        const directory = path.join(destination, 'out', 'profile')
        const stages = readJSON(path.join(directory, 'stages.json'))
        const { total_wall_s } = readJSON(path.join(directory, 'total_wall_s.json'))
        const gpuUtil = readJSON(path.join(directory, 'gpu_util.json'))
        if (!Number.isFinite(total_wall_s) || total_wall_s <= 0 || !Array.isArray(stages)
          || !stages.every(item => item && typeof item.stage === 'string' && item.stage.trim()
            && (item.kind === undefined || ['compute', 'transfer', 'other'].includes(item.kind))
            && Number.isFinite(item.wall_s) && item.wall_s >= 0
            && (item.gpu_s === null || (Number.isFinite(item.gpu_s) && item.gpu_s >= 0)))
          || !Array.isArray(gpuUtil) || !gpuUtil.every(item => item && nonnegative(item.t)
            && nonnegative(item.util) && item.util <= 100)) return 'parse'
        const timedWall = stages.reduce((sum, item) => sum + item.wall_s, 0)
        if (!Number.isFinite(timedWall)) return 'parse'
        const measuredStages = stages.map(({ stage, kind, wall_s, gpu_s, start_s }) => {
          if (start_s !== undefined && (!nonnegative(start_s) || !Number.isFinite(start_s + wall_s))) {
            throw new Error('invalid stage window')
          }
          const samples = start_s === undefined ? [] : gpuUtil.filter(item => item.t >= start_s && item.t < start_s + wall_s)
          return { stage, ...(kind === undefined ? {} : { kind }), wall_s, gpu_s,
            start_s: start_s ?? null, wall_fraction: Math.min(1, wall_s / total_wall_s),
            mean_gpu_util: samples.length ? samples.reduce((sum, item) => sum + item.util / 100, 0) / samples.length : null }
        })
        let allocation
        try { allocation = readJSON(path.join(C, 'box.json')) } catch { /* Probe supplies inventory. */ }
        const allocationCount = Number.isInteger(allocation?.gpu_count) && allocation.gpu_count >= 0
          ? allocation.gpu_count : Number(/^gpu_(\d+)x_/.exec(allocation?.type)?.[1])
        facts.profile_complete = true
        facts.timed_fraction = Math.min(1, timedWall / total_wall_s)
        facts.gpu_telemetry = gpuUtil.length > 0
        writeFileSync(path.join(A, 'profile-packet.json'), JSON.stringify({
          stages: measuredStages, total_wall_s, concurrency: null,
          timed_fraction: facts.timed_fraction, gpu_telemetry: facts.gpu_telemetry,
          gpu_count: Number.isInteger(allocationCount) && allocationCount >= 0 ? allocationCount
            : Array.isArray(boxProbe?.nvidia?.gpus) ? boxProbe.nvidia.gpus.length : 1,
        }, null, 2) + '\n')
        const processWrapper = stages.some(item => /(?:^|[\s_-])(?:process|wrapper|telemetry|total|overall)(?:$|[\s_-])/i.test(item.stage)
          || (item.wall_s >= total_wall_s * 0.98 && item.wall_s <= total_wall_s * 1.02))
        return stages.length >= 3 && !processWrapper && facts.timed_fraction >= 0.9 && facts.gpu_telemetry
          ? null : 'numeric'
      } catch {
        return 'parse'
      }
    }
