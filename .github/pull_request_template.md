## Task Contribution

### Proposal

- Proposal URL:
- Proposal approval status:

### Task Identity

- Task ID:
- Task title:
- Source URL:
- Base revision:

### Structure

- Modules:
- Units:
- Dependency DAG summary:
- Source evidence for dependency edges:

### Gold / Verification

- Gold solution or gold patch strategy:
- Full-task testing strategy:
- Unit-level verification strategy:
- Why the verifier rejects partial / incorrect implementations:

### Local Validation

Paste the commands you ran and summarize the results:

```bash
python3 scripts/validate_task_contribution.py --task-dir tasks/<task-id> --static-only
loopsbench tasks validate --task-id <task-id>
loopsbench run --agent oracle --task-id <task-id> --dataset-path tasks --docker-image-strategy local-build
```

### Licensing / Redistribution

- License status:
- Redistribution notes:

### Known Limitations

- 

## Checklist

- [ ] This PR links an approved Task Proposal issue.
- [ ] This PR changes one task only, or maintainers explicitly approved a broader change.
- [ ] `task.yaml`, DAG files, requirements, tests, and gold patches are included.
- [ ] Static validation passed locally.
- [ ] Oracle passed locally.
- [ ] The task does not expose hidden tests or gold patches in `base/`.
- [ ] The task is grounded in a real source and includes source evidence.
