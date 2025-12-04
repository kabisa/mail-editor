# Domain ID Implementation Summary

## Overview
This document summarizes the implementation of the `domain_id` feature for the Mail Editor package, enabling multi-tenant email template management.

## Changes Made

### 1. Database Migration
**File**: `mail_editor/migrations/0014_mailtemplate_domain_id.py`
- Added `domain_id` field to `MailTemplate` model
- Type: `IntegerField` with default value of 1
- Non-nullable field to ensure data integrity

### 2. Model Updates
**File**: `mail_editor/models.py`

#### MailTemplateManager Changes:
- **`get_for_language(template_type, language, domain_id=None)`**: 
  - Added optional `domain_id` parameter
  - Filters templates by domain when provided
  - Maintains backward compatibility (domain_id defaults to None)

- **`get_for_domain(template_type, domain_id, language=None)`** (NEW):
  - New method for explicit domain-based template retrieval
  - Optionally filters by language
  - Returns first matching template or raises `DoesNotExist`

#### MailTemplate Model Changes:
- **`clean()` method**: Updated uniqueness validation
  - Now enforces uniqueness per (template_type, language, domain_id)
  - Previously: (template_type, language)
  - Updated error message to reflect new constraint

### 3. Helper Functions
**File**: `mail_editor/helpers.py`

#### `find_template()` Updates:
- Added `domain_id` parameter (defaults to None)
- Uses `settings.DEFAULT_DOMAIN_ID` when domain_id is None
- Creates/retrieves templates with domain_id in filters
- Maintains backward compatibility for existing code

### 4. Settings
**File**: `mail_editor/settings.py`

#### New Setting:
- **`MAIL_EDITOR_DEFAULT_DOMAIN_ID`**: 
  - Configurable default domain_id
  - Defaults to 1 if not specified
  - Used by `find_template()` when no domain_id provided

### 5. Admin Interface
**File**: `mail_editor/admin.py`

#### Updates:
- Added `domain_id` to `list_display` (visible in template list)
- Added `domain_id` to `list_filter` (filterable in admin)
- Added `domain_id` to fieldsets (editable in template form)
- Position: After language, before preview link

### 6. Management Command
**File**: `mail_editor/management/commands/add_missing_templates.py`

#### New Feature:
- Added `--domain-id` command-line argument
  - Type: integer
  - Optional parameter
  - When provided, creates templates with specified domain_id
  - When omitted, uses `MAIL_EDITOR_DEFAULT_DOMAIN_ID` setting

**Usage Examples**:
```bash
# Create templates for domain 1 (default)
python manage.py add_missing_templates

# Create templates for domain 2
python manage.py add_missing_templates --domain-id=2

# Create templates for domain 5
python manage.py add_missing_templates --domain-id 5
```

### 7. Test Suite
**File**: `tests/test_domain_id.py` (NEW)

#### Test Coverage:
1. **test_create_template_with_domain_id**: Template creation with specific domain_id
2. **test_create_template_default_domain_id**: Template creation with default domain_id
3. **test_create_template_custom_default_domain_id**: Custom default from settings
4. **test_multiple_templates_different_domains**: Same type across domains
5. **test_template_with_language_and_domain**: Language + domain combinations
6. **test_get_for_language_with_domain_id**: Manager method with domain filtering
7. **test_get_for_domain**: New manager method testing
8. **test_get_for_domain_with_language**: Domain + language retrieval
9. **test_unique_constraint_with_domain**: Uniqueness enforcement
10. **test_validation_unique_with_domain**: Validation error handling
11. **test_send_email_with_domain**: Email sending with domain templates
12. **test_filter_templates_by_domain**: QuerySet filtering by domain

## Usage Examples

### Basic Usage
```python
from mail_editor.helpers import find_template

# Use default domain (domain_id=1)
template = find_template('activation')

# Specify domain explicitly
template = find_template('activation', domain_id=2)

# With language and domain
template = find_template('activation', language='nl', domain_id=3)
```

### Manager Methods
```python
from mail_editor.models import MailTemplate

# Get template by language and domain
template = MailTemplate.objects.get_for_language(
    'activation', 
    'en', 
    domain_id=2
)

# Get template by domain (with optional language)
template = MailTemplate.objects.get_for_domain(
    'activation',
    domain_id=2,
    language='en'  # optional
)
```

### Sending Emails
```python
# Find domain-specific template
template = find_template('activation', domain_id=2)

# Send email using domain template
template.send_email(
    to_addresses=['user@example.com'],
    context={
        'name': 'John Doe',
        'activation_link': 'https://example.com/activate/token',
    }
)
```

### Configuration
```python
# settings.py

# Set default domain ID for all templates
MAIL_EDITOR_DEFAULT_DOMAIN_ID = 2

# Templates configuration (unchanged)
MAIL_EDITOR_CONF = {
    'activation': {
        'name': 'Activation Email',
        'description': 'Sent when users need to activate their account',
        'subject_default': 'Activate your account',
        'body_default': '<h1>Welcome!</h1>',
        'subject': [...],
        'body': [...],
    },
}
```

## Migration Guide

### For Existing Installations:

1. **Run Migration**:
   ```bash
   python manage.py migrate
   ```
   - All existing templates will get `domain_id=1`

2. **Update Code (Optional)**:
   - No code changes required if using single domain
   - Existing `find_template()` calls work unchanged
   - Add `domain_id` parameter only for multi-tenant setups

3. **Create Domain-Specific Templates**:
   ```bash
   # Create templates for additional domains
   python manage.py add_missing_templates --domain-id=2
   python manage.py add_missing_templates --domain-id=3
   ```

### For Multi-Tenant Applications:

1. **Determine Domain Context**:
   - Add logic to determine current domain/tenant
   - Pass domain_id when retrieving templates

2. **Update Template Retrieval**:
   ```python
   # Before
   template = find_template('activation', language='en')
   
   # After
   domain_id = get_current_domain_id()  # Your logic
   template = find_template('activation', language='en', domain_id=domain_id)
   ```

3. **Admin Usage**:
   - Use domain_id filter in admin to view domain-specific templates
   - Create/edit templates for different domains via admin interface

## Backward Compatibility

- **Fully backward compatible** for single-domain installations
- Existing code continues to work without modifications
- Default domain_id of 1 matches previous behavior
- No breaking changes for existing API consumers

## Technical Notes

### Database Schema:
```sql
ALTER TABLE mail_editor_mailtemplate 
ADD COLUMN domain_id INTEGER NOT NULL DEFAULT 1;
```

### Uniqueness Constraint:
Templates are unique per combination of:
- `template_type`
- `language` 
- `domain_id`

This allows same template type/language for different domains.

### Performance Considerations:
- Consider adding database index on `domain_id` for large deployments:
  ```python
  # In future migration if needed
  migrations.AddIndex(
      model_name='mailtemplate',
      index=models.Index(fields=['domain_id', 'template_type'])
  )
  ```

## Testing

Run the test suite to verify domain_id functionality:
```bash
# Run all tests
pytest

# Run domain_id specific tests
pytest tests/test_domain_id.py

# Run with coverage
pytest --cov=mail_editor tests/
```

## Future Enhancements

Potential improvements for future versions:
1. Add database index on domain_id for better query performance
2. Add domain_id to Meta.unique_together constraint
3. Create domain management interface in admin
4. Add domain-based permission checks
5. Support domain inheritance/fallback logic

## Support

For issues or questions:
- GitHub Issues: https://github.com/maykinmedia/mail-editor/issues
- Review tests in `tests/test_domain_id.py` for usage examples
