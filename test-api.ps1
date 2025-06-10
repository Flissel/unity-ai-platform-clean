$headers = @{
    'Authorization' = 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4OTI3MDE4NC1jYjIyLTQwZGQtYTljMS1hNjVlMzgxMjFjY2EiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzQ5MTk0MDE2fQ.VgtrtX9jNjYj5z_WfHo2Lv9Flm9bQuB1hSY_JfITlKI'
    'Content-Type' = 'application/json'
}

try {
    Write-Host "Testing n8n API connection..."
    $response = Invoke-WebRequest -Uri 'https://n8n.unit-y-ai.io/api/v1/workflows' -Headers $headers -UseBasicParsing
    Write-Host "Status Code: $($response.StatusCode)"
    Write-Host "Response Length: $($response.Content.Length) characters"
    Write-Host "First 500 characters of response:"
    Write-Host $response.Content.Substring(0, [Math]::Min(500, $response.Content.Length))
} catch {
    Write-Host "Error occurred:"
    Write-Host "Message: $($_.Exception.Message)"
    Write-Host "Status Code: $($_.Exception.Response.StatusCode)"
    Write-Host "Response: $($_.Exception.Response)"
}