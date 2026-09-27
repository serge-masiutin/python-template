# File Uploads

File upload handling for Inertia.js + Django with configured Django storage.

## Table of Contents

- [Basic Upload with Form Component](#basic-upload-with-form-component)
- [Upload with useForm](#upload-with-useform)
- [Progress Tracking](#progress-tracking)
- [configured Django storage Backend](#active-storage-backend)
- [Multiple Files](#multiple-files)
- [Image Preview](#image-preview)
- [Direct Uploads](#direct-uploads)

---

## Basic Upload with Form Component

Inertia auto-detects file inputs and switches to `multipart/form-data`.

```tsx
<Form method="post" action="/avatars">
  {({ progress, processing }) => (
    <>
      <input type="file" name="avatar" accept="image/*" />
      {progress && (
        <progress value={progress.percentage} max="100">
          {progress.percentage}%
        </progress>
      )}
      <button type="submit" disabled={processing}>Upload</button>
    </>
  )}
</Form>
```

No manual `FormData` construction needed. No special headers.

## Upload with useForm

```tsx
const form = useForm<{ avatar: File | null }>({
  avatar: null,
})

const handleSubmit = (e: React.FormEvent) => {
  e.preventDefault()
  form.post('/avatars', {
    forceFormData: true, // ensure FormData even if no file selected
  })
}

return (
  <form onSubmit={handleSubmit}>
    <input
      type="file"
      onChange={e => form.setData('avatar', e.target.files?.[0] ?? null)}
    />
    {form.progress && (
      <progress value={form.progress.percentage} max="100" />
    )}
    <button disabled={form.processing}>Upload</button>
  </form>
)
```

## Progress Tracking

Both `<Form>` and `useForm` provide upload progress automatically.

```tsx
// Form component
<Form method="post" action="/documents" onProgress={(progress) => {
  console.log(`${progress.percentage}% uploaded`)
}}>
  {({ progress }) => (
    progress && <ProgressBar value={progress.percentage} />
  )}
</Form>
```

The `progress` object:
```typescript
{
  percentage: number  // 0-100
  total: number       // total bytes
  loaded: number      // bytes uploaded
}
```

## configured Django storage Backend

```python
class AvatarForm(forms.Form):
    avatar = forms.FileField()

    def clean_avatar(self):
        upload = self.cleaned_data["avatar"]
        if upload.size > 2 * 1024 * 1024:
            raise forms.ValidationError("Use a file smaller than 2 MiB")
        return upload

@require_POST
@login_required
def upload_avatar(request):
    form = AvatarForm(request.POST, request.FILES)
    if not form.is_valid():
        return invalid_form(request, form, destination="profile")
    # Storage and content verification belong to an implemented upload boundary.
    store_verified_avatar(actor=request.user, upload=form.cleaned_data["avatar"])
    messages.success(request, "Avatar uploaded")
    return redirect_303("profile")
```

Strong parameters for files:
```python
form = AvatarForm(request.POST, request.FILES)
# Authenticate, enforce count/size limits, verify content and isolate untrusted files.
# File extension and browser Content-Type alone do not establish safety.
```

## Multiple Files

```tsx
<Form method="post" action="/documents">
  {({ progress }) => (
    <>
      <input type="file" name="documents[]" multiple />
      {progress && <progress value={progress.percentage} max="100" />}
      <button type="submit">Upload All</button>
    </>
  )}
</Form>
```

Django side:
```python
uploads = request.FILES.getlist("documents")
if not 1 <= len(uploads) <= 10:
    return HttpResponseBadRequest("Upload between one and ten documents")
# Validate each upload before storing any. Define cleanup for partial storage failures.
validated = [validate_document(upload) for upload in uploads]
store_documents(actor=request.user, uploads=validated)
messages.success(request, "Documents uploaded")
return redirect_303("documents")
```

## Image Preview

`useState` for preview is local UI state — still use `<Form>`, not `useForm`:

```tsx
function AvatarUpload() {
  const [preview, setPreview] = useState<string | null>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setPreview(URL.createObjectURL(file))
    }
  }

  return (
    <Form method="post" action="/avatars">
      {({ progress, processing }) => (
        <>
          {preview && <img src={preview} alt="Preview" className="w-24 h-24 rounded-full" />}
          <input type="file" name="avatar" accept="image/*" onChange={handleFileChange} />
          {progress && <progress value={progress.percentage} max="100" />}
          <button type="submit" disabled={processing}>Upload</button>
        </>
      )}
    </Form>
  )
}
```

## Direct Uploads

For large files, use configured Django storage direct uploads to upload directly
to the storage service (S3, GCS) instead of through the Django server.

```tsx
import { DirectUpload } from '@rails/activestorage'

function uploadFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const upload = new DirectUpload(file, '/rails/active_storage/direct_uploads')
    upload.create((error, blob) => {
      if (error) reject(error)
      else resolve(blob.signed_id)
    })
  })
}
```

Then submit the signed ID via Inertia form:
```tsx
const form = useForm({ avatar: '' })

const handleFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
  const file = e.target.files?.[0]
  if (file) {
    const signedId = await uploadFile(file)
    form.setData('avatar', signedId)
  }
}
```
