# Semantic Versioning (SemVer) Policy

## Përmbledhje

Smart Grid Analytics përdor Semantic Versioning (SemVer) për versioning të releases, duke siguruar komunikim të qartë për breaking dhe non-breaking changes.

## Format

**MAJOR.MINOR.PATCH**

- **MAJOR**: Breaking changes (incompatible API changes)
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## Examples

- `1.0.0` - Initial release
- `1.0.1` - Bug fix (backward compatible)
- `1.1.0` - New feature (backward compatible)
- `2.0.0` - Breaking change (incompatible)

## Versioning Rules

### MAJOR Version (Breaking Changes)

Increment MAJOR version when:
- API endpoints are removed
- API request/response formats change incompatibly
- Database schema changes break existing queries
- Configuration file formats change
- Dependencies are upgraded with breaking changes

**Examples:**
- `/api/v1/users` → `/api/v2/users` (new version)
- `POST /api/v1/users` request body format changes
- Database column removed
- Environment variable renamed

### MINOR Version (New Features)

Increment MINOR version when:
- New API endpoints are added
- New optional fields are added to requests/responses
- New features are added (backward compatible)
- New configuration options are added
- Performance improvements

**Examples:**
- New endpoint: `GET /api/v1/analytics/new-feature`
- New optional field in response: `{"user": {...}, "metadata": {...}}`
- New Kafka topic added
- New environment variable (optional)

### PATCH Version (Bug Fixes)

Increment PATCH version when:
- Bug fixes are applied
- Security patches
- Documentation updates
- Code refactoring (no behavior change)
- Dependency updates (non-breaking)

**Examples:**
- Fix memory leak
- Fix authentication bug
- Update documentation
- Security vulnerability patch

## Version Tags

### Git Tags

```bash
# Create version tag
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# List tags
git tag -l

# Checkout specific version
git checkout v1.0.0
```

### Docker Image Tags

```bash
# Tag Docker image
docker tag smartgrid-api-gateway:latest smartgrid-api-gateway:1.0.0
docker tag smartgrid-api-gateway:latest smartgrid-api-gateway:1.0
docker tag smartgrid-api-gateway:latest smartgrid-api-gateway:1

# Push tags
docker push smartgrid-api-gateway:1.0.0
docker push smartgrid-api-gateway:1.0
docker push smartgrid-api-gateway:1
```

## Release Process

### 1. Pre-Release Checklist

- [ ] All tests pass
- [ ] Code review completed
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version numbers updated in code
- [ ] Security scan passed

### 2. Version Bump

Update version in:
- `package.json` (if applicable)
- `setup.py` (if applicable)
- `VERSION` file
- `CHANGELOG.md`
- Docker image tags
- Kubernetes manifests

### 3. Create Release

```bash
# Update version
echo "1.0.0" > VERSION

# Commit version bump
git add VERSION CHANGELOG.md
git commit -m "Bump version to 1.0.0"

# Create tag
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push
git push origin main
git push origin v1.0.0
```

### 4. Release Notes

Create release notes with:
- Version number
- Release date
- Changes (MAJOR, MINOR, PATCH)
- Migration guide (if MAJOR)
- Breaking changes (if MAJOR)

## CHANGELOG Format

```markdown
# Changelog

## [1.0.0] - 2024-01-15

### Added
- Initial release
- API Gateway service
- Data Ingestion service

### Changed
- Updated dependencies

### Fixed
- Fixed authentication bug

## [0.9.0] - 2024-01-10

### Added
- Analytics service
- Notification service
```

## API Versioning

### URL Versioning

```
/api/v1/users
/api/v2/users
```

### Header Versioning (Alternative)

```
Accept: application/vnd.smartgrid.v1+json
Accept: application/vnd.smartgrid.v2+json
```

### Best Practice

- Use URL versioning for REST APIs
- Maintain at least 2 versions simultaneously
- Deprecate old versions with 6-month notice
- Provide migration guides

## Backward Compatibility

### Breaking Changes (MAJOR)

- Remove endpoints
- Change required fields
- Change response format
- Remove configuration options

### Non-Breaking Changes (MINOR/PATCH)

- Add new endpoints
- Add optional fields
- Add new configuration options
- Performance improvements
- Bug fixes

## Version Management Tools

### Automated Versioning

```bash
# Using bump2version
pip install bump2version

# Bump patch version
bump2version patch

# Bump minor version
bump2version minor

# Bump major version
bump2version major
```

### CI/CD Integration

```yaml
# .github/workflows/release.yml
- name: Bump version
  run: |
    VERSION=$(bump2version --dry-run --list patch | grep new_version | sed -r s,"^.*=",,)
    echo "VERSION=$VERSION" >> $GITHUB_ENV

- name: Create tag
  run: |
    git tag -a v${{ env.VERSION }} -m "Release v${{ env.VERSION }}"
    git push origin v${{ env.VERSION }}
```

## Examples

### Example 1: Bug Fix (PATCH)

**Before**: `1.0.0`  
**After**: `1.0.1`

**Change**: Fixed memory leak in data processing service

### Example 2: New Feature (MINOR)

**Before**: `1.0.0`  
**After**: `1.1.0`

**Change**: Added new analytics endpoint `/api/v1/analytics/predictions`

### Example 3: Breaking Change (MAJOR)

**Before**: `1.0.0`  
**After**: `2.0.0`

**Change**: Removed deprecated endpoint `/api/v1/legacy/users`

## Best Practices

1. **Always use SemVer**: Never skip versions
2. **Document Changes**: Update CHANGELOG.md
3. **Test Compatibility**: Test backward compatibility
4. **Migration Guides**: Provide guides for MAJOR changes
5. **Deprecation Policy**: 6-month notice for breaking changes
6. **Version Tags**: Tag all releases in Git
7. **Automation**: Automate version bumping in CI/CD

