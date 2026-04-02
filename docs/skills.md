# vcsx Skills Reference

vcsx generates 20+ skills for Claude Code projects. Each skill is a workflow that the AI can use.

## Git Workflow Skills

### /commit-message
Generates conventional commit messages from git diff.
- **Use**: When committing changes
- **Trigger**: Auto or manual

### /pr-review
Reviews PRs against team standards.
- **Use**: Before creating PR
- **Trigger**: Auto or manual

### /squash
Squashes multiple commits into one.
- **Use**: Before merging feature branch
- **Trigger**: Manual

### /revert
Reverts specific commits.
- **Use**: Undo committed changes
- **Trigger**: Manual

## Deployment Skills

### /deploy
Deploys to hosting provider.
- **Use**: When deploying
- **Trigger**: Manual
- **Config**: Uses ctx.hosting

### /rollback
Rolls back deployment.
- **Use**: When deployment fails
- **Trigger**: Manual

## Database Skills

### /migration
Generates database migrations.
- **Use**: Creating schema changes
- **Trigger**: Manual

### /orm-conventions
ORM patterns and conventions.
- **Use**: When defining models
- **Trigger**: Auto

### /query-optimization
Database query optimization.
- **Use**: Optimizing performance
- **Trigger**: Manual

## DevOps Skills

### /docker-conventions
Docker best practices.
- **Use**: Containerizing apps
- **Trigger**: Auto

### /k8s-conventions
Kubernetes patterns.
- **Use**: Deploying to K8s
- **Trigger**: Auto

### /ci-cd-builder
Builds CI/CD pipelines.
- **Use**: Setting up pipelines
- **Trigger**: Manual

## Testing Skills

### /test-patterns
Test writing conventions.
- **Use**: Writing tests
- **Trigger**: Auto

### /mutation-testing
Mutation testing setup.
- **Use**: Validating test quality
- **Trigger**: Manual

### /e2e-patterns
End-to-end testing patterns.
- **Use**: Writing E2E tests
- **Trigger**: Auto

## API Skills

### /api-conventions
REST API design patterns.
- **Use**: Creating/modifying APIs
- **Trigger**: Auto (for API projects)

### /openapi-generator
Generates from OpenAPI specs.
- **Use**: Building APIs
- **Trigger**: Manual

### /grpc-conventions
gRPC service patterns.
- **Use**: Building gRPC services
- **Trigger**: Auto

## Security Skills

### /security-review
Reviews code for vulnerabilities.
- **Use**: Before merging
- **Trigger**: Auto or manual

### /auth-conventions
Auth patterns and flows.
- **Use**: Working with auth code
- **Trigger**: Auto (for auth projects)

## Quality Skills

### /refactor
Suggests code improvements.
- **Use**: When improving code
- **Trigger**: Manual

### /performance
Performance optimization.
- **Use**: Optimizing performance
- **Trigger**: Manual

### /debt-analyzer
Analyzes technical debt.
- **Use**: Assessing code quality
- **Trigger**: Manual
