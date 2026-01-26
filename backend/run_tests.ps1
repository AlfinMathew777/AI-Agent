$Headers = @{ "x-admin-key" = "secret-admin-key" }

# Test 1: Security (Unauthorized) - Expected 401
Write-Host "Test 1: Security (Unauthorized)"
try {
    Invoke-RestMethod -Uri "http://localhost:8002/admin/index/status" -Method Get -ErrorAction Stop
} catch {
    Write-Host "Success: Got expected error: $($_.Exception.Message)"
}
Write-Host "`n----------------`n"

# Test 2: Security (Authorized) - Expected 200
Write-Host "Test 2: Security (Authorized)"
$status = Invoke-RestMethod -Uri "http://localhost:8002/admin/index/status" -Method Get -Headers $Headers
Write-Host "Status: $($status | ConvertTo-Json -Depth 2)"
Write-Host "`n----------------`n"

# Test 3: Upload File
Write-Host "Test 3: Upload File"
"This is a test file content for RAG." | Out-File -Encoding utf8 test_upload.md
$uploadUri = "http://localhost:8002/admin/upload"
# Uploading files via Invoke-RestMethod is tricky, skipping file upload test via script for now or use curl.exe explicitly if available.
# Let's use curl.exe if available (git bash or windows native curl)
if (Get-Command curl.exe -ErrorAction SilentlyContinue) {
    Write-Host "Using native curl.exe for upload..."
    & curl.exe -s -H "x-admin-key: secret-admin-key" -F "audience=guest" -F "file=@test_upload.md" "$uploadUri"
} else {
    Write-Host "Skipping upload test (curl.exe not found)"
}
Write-Host "`n----------------`n"

# Test 4: Reindex Knowledge Base
Write-Host "Test 4: Reindex Knowledge Base"
$reindex = Invoke-RestMethod -Uri "http://localhost:8002/admin/reindex?audience=guest" -Method Post -Headers $Headers
Write-Host "Reindex: $($reindex | ConvertTo-Json -Depth 2)"
Write-Host "`n----------------`n"

# Test 5: List Files
Write-Host "Test 5: List Files"
$files = Invoke-RestMethod -Uri "http://localhost:8002/admin/files" -Method Get -Headers $Headers
Write-Host "Files: $($files | ConvertTo-Json -Depth 2)"
Write-Host "`n----------------`n"

# Test 6: Delete File and Vectors
Write-Host "Test 6: Delete File and Vectors"
try {
    $del = Invoke-RestMethod -Uri "http://localhost:8002/admin/files/guest/test_upload.md" -Method Delete -Headers $Headers
    Write-Host "Delete: $($del | ConvertTo-Json -Depth 2)"
} catch {
    Write-Host "Delete failed: $($_.Exception.Message)"
}
Write-Host "`n----------------`n"

# Test 7: Verify Deletion
Write-Host "Test 7: Verify Deletion"
$files2 = Invoke-RestMethod -Uri "http://localhost:8002/admin/files" -Method Get -Headers $Headers
Write-Host "Files after delete: $($files2 | ConvertTo-Json -Depth 2)"
Write-Host "`n----------------`n"
