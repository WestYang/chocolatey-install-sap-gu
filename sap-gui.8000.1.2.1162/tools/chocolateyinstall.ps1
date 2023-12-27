# 定义API端点和参数
$apiEndpoint = 'http://systeminfo.leadchina.cn/sap_install_status'
$timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
$computerName = $env:COMPUTERNAME
$status = 'success'
$errorMessage = $null

# 尝试安装Chocolatey包
try {
    # 定义Chocolatey包参数
    $packageArgs = @{
        packageName    = $env:ChocolateyPackageName
        url64          = 'http://download-soft.lead.cn/sap-gui/GUI800_2-80006342.EXE'
        checksum64     = '8b13c42545a58397549d2bbee73e6f1d65094612d3edc73f7814cfc9763d0147'
        checksumtype64 = 'SHA256'
        fileType       = 'EXE'
        silentArgs     = '/product="SAPGUI64" /silent'
        validExitCodes = @(0, 129)
    }

    # 安装Chocolatey包
    Install-ChocolateyPackage @packageArgs
} catch {
    # 在失败时更新状态和错误消息
    $status = 'failure'
    $errorMessage = $_.Exception.Message
} finally {
    # 构建JSON负载
    $jsonPayload = @{
        Timestamp    = $timestamp
        ComputerName = $computerName
        Status       = $status
        ErrorMessage = $errorMessage
    } | ConvertTo-Json

    # 尝试调用API接口，但即使失败也不中断主要软件安装
    try {
        Invoke-WebRequest -Uri $apiEndpoint -Method Post -Body $jsonPayload -ContentType 'application/json'
        Write-Host "API请求成功。"
    } catch {
        Write-Host "API请求失败。错误信息：$($_.Exception.Message)"
    }
}




# XML内容
$landscapeXmlContent = '<?xml version="1.0"?>
<Landscape updated="2023-07-18T02:28:29Z" version="1" generator="SAP GUI for Windows v8000.1.2.155">
  <Includes>
    <Include url="file:///C:/Users/Administrator/AppData/Roaming/SAP/Common/SAPUILandscapeGlobal.xml" index="0" description="SAP reserved"/>
  </Includes>
  <Workspaces>
    <Workspace uuid="30fb218d-29d6-4cdc-88c2-405e94185b06" name="Local">
      <Item uuid="c61a6878-2cbc-4f1a-a98c-ea6285fbee98" serviceid="01c209e6-19de-4ab9-a409-0a92151e6b21"/>
      <Item uuid="d7a0f890-3976-44f0-845a-051aed6f3c7d" serviceid="41e81fc9-6769-4922-8d3d-18a70e2db334"/>
    </Workspace>
  </Workspaces>
  <Services>
    <Service type="SAPGUI" uuid="01c209e6-19de-4ab9-a409-0a92151e6b21" name="S4D" systemid="S4D" mode="1" server="s4-dev.leadchina.cn:3200" sncop="-1" dcpg="2"/>
    <Service type="SAPGUI" uuid="41e81fc9-6769-4922-8d3d-18a70e2db334" name="S4Q" systemid="SSS" mode="1" server="s4-qas.leadchina.cn:3200" sncop="-1" dcpg="2"/>
  </Services>
  <Messageservers>
    <Messageserver uuid="2c5c657d-6e71-4e64-8496-cb6579b89bfc" name="S4D" host="s4-dev.leadchina.cn"/>
    <Messageserver uuid="f3304fe1-518f-48e4-affa-11411e71f15c" name="S4Q" host="s4-qas.leadchina.cn"/>
  </Messageservers>
</Landscape>'

$landscapeGlobalXmlContent = '<?xml version="1.0"?>
<Landscape><Messageservers/></Landscape>'

## 获取%APPDATA%环境变量值
#$appDataPath = [Environment]::GetFolderPath('ApplicationData')

#获取所有用户文件夹
$usersFolder = Get-ChildItem -Path  C:\Users -Directory

#遍历每个用户文件夹
foreach ($userFolder in $usersFolder) {
  $landscapeXmlPath = Join-Path $userFolder.FullName 'AppData\Roaming\SAP\Common\SAPUILandscape.xml'
  $landscapeGlobalXmlPath = Join-Path $userFolder.FullName 'AppData\Roaming\SAP\Common\SAPUILandscapeGlobal.xml'
  
  New-Item -ItemType Directory -Path (Join-Path $userFolder.FullName 'AppData\Roaming\SAP\Common') -Force
  Set-Content -Path $landscapeXmlPath -Value $landscapeXmlContent
  Set-Content -Path $landscapeGlobalXmlPath -Value $landscapeGlobalXmlContent
}

## 完整路径
#$landscapeXmlPath = Join-Path $appDataPath 'SAP\Common\SAPUILandscape.xml'
#$landscapeGlobalXmlPath = Join-Path $appDataPath 'SAP\Common\SAPUILandscapeGlobal.xml'



## 创建文件夹和写入文件
#New-Item -ItemType Directory -Path (Join-Path $appDataPath 'SAP\Common') -Force
#Set-Content -Path $landscapeXmlPath -Value $landscapeXmlContent
#Set-Content -Path $landscapeGlobalXmlPath -Value $landscapeGlobalXmlContent
