(function trainingWorkoutModel(root) {
  "use strict";
  const number = value => value === null || value === undefined || String(value).trim() === "" ? null : Number(value);
  const clone = value => JSON.parse(JSON.stringify(value));
  function targets(exercise) {
    if (Array.isArray(exercise.setTargets) && exercise.setTargets.length) return clone(exercise.setTargets);
    return Array.from({length: Math.min(20, Math.max(1, Number(exercise.targetSets) || 3))}, () => ({
      reps: String(exercise.targetReps || "8-10"), weight: number(exercise.targetWeight),
      rir: number(exercise.targetRir), rpe: number(exercise.targetRpe)
    }));
  }
  function validTargets(rows) {
    return Array.isArray(rows) && rows.length >= 1 && rows.length <= 20 && rows.every(row => {
      const reps = String(row.reps).split("-").map(Number);
      return /^[1-9][0-9]{0,2}(?:-[1-9][0-9]{0,2})?$/.test(row.reps) && (reps.length === 1 || reps[1] >= reps[0]) &&
        ["weight","rir","rpe"].every(key => {
          const n = number(row[key]);
          return n === null || Number.isFinite(n) && n >= (key === "rpe" ? 1 : 0) && n <= (key === "weight" ? 10000 : 10) &&
            (key !== "rir" || Number.isInteger(n));
        });
    });
  }
  function groups(exercises) {
    const result = [];
    for (const [index, exercise] of exercises.entries()) {
      const last = result.at(-1);
      if (exercise.supersetId && last?.id === exercise.supersetId) last.indices.push(index);
      else result.push({id:exercise.supersetId || "",indices:[index]});
    }
    return result;
  }
  function sequence(exercises) {
    const result = [];
    for (const group of groups(exercises)) {
      const rounds = Math.max(...group.indices.map(i => targets(exercises[i]).length));
      for (let round=1;round<=rounds;round++) {
        const indices = group.indices.filter(i => targets(exercises[i]).length >= round);
        indices.forEach((i,n) => result.push({exerciseIndex:i,setIndex:round,
          restSeconds:n===indices.length-1 ? Number(group.id ? exercises[i].supersetRestSeconds ?? 90 : exercises[i].restSeconds ?? 90) : 0,
          groupId:group.id}));
      }
    }
    return result;
  }
  const key = (exercise,index) => (exercise.key || exercise.id || exercise.slug)+"__"+index;
  const registered = log => !!log?.completedAt && (log.localRegistered === true || !!log.syncedAt);
  function next(session, exerciseIndex, setIndex) {
    const steps=sequence(session.plannedExercises), start=steps.findIndex(s=>s.exerciseIndex===exerciseIndex&&s.setIndex===setIndex);
    const nextStep=steps.slice(start+1).find(s=>!registered(session.setLogs[key(session.plannedExercises[s.exerciseIndex],s.setIndex)]));
    return nextStep || {exerciseIndex:-1,setIndex:1,restSeconds:0};
  }
  function previous(history, exercise, startedAt) {
    const id=exercise.exerciseId;
    if (!id) return [];
    const latest=history.filter(h=>h.completedAt && (!startedAt || Date.parse(h.completedAt)<Date.parse(startedAt)))
      .sort((a,b)=>String(b.completedAt).localeCompare(String(a.completedAt)) || String(b.id).localeCompare(String(a.id)))
      .find(h=>(h.sets||[]).some(s=>(s.exerciseId||s.exercise_id)===id));
    const matches=(latest?.sets||[]).filter(s=>(s.exerciseId||s.exercise_id)===id);
    if (!matches.length) return [];
    // A repeated exercise inside a prior workout is not a different equipment/variant.
    // Use one planned occurrence, never combine two occurrences into a fabricated set list.
    const occurrences=[...new Set(matches.map(s=>s.plannedExerciseKey||s.planned_exercise_key))].sort();
    const occurrence=occurrences.includes(exercise.key) ? exercise.key : occurrences[0];
    return matches.filter(s=>(s.plannedExerciseKey||s.planned_exercise_key)===occurrence)
      .sort((a,b)=>(a.setIndex??a.set_index)-(b.setIndex??b.set_index));
  }
  const displayWeight=(kg,imperial)=>number(kg)===null ? "" : Math.round(number(kg)*(imperial?2.2046226218:1)*100)/100;
  const storedWeight=(value,imperial)=>number(value)===null ? null : Math.round(number(value)/(imperial?2.2046226218:1)*1000000)/1000000;
  const api={number,clone,targets,validTargets,groups,sequence,key,registered,next,previous,displayWeight,storedWeight};
  if(typeof module!=="undefined"&&module.exports)module.exports=api;
  else root.FMZ_WORKOUT_MODEL=Object.freeze(api);
})(typeof window!=="undefined"?window:globalThis);
