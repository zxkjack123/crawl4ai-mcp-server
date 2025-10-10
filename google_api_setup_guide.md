# Google Custom Search API 配置指南

## 概述

本指南整合了多个来源的信息，帮助您获取 Google Custom Search API Key 和 CSE ID。

---

## 搜索结果汇总

### 查询: Google Cloud Console Custom Search API key tutorial

1. **[Google](https://www.google.com/)**
   Search the world's information, including webpages, images, videos and more. Google has many special features to help you find exactly what you're looking for.

2. **[Sign in - Google Accounts](https://accounts.google.com/)**
   Not your computer? Use a private browsing window to sign in. Learn more about using Guest mode

3. **[Google Maps](https://maps.google.com/)**
   Find local businesses, view maps and get driving directions in Google Maps.

4. **[Google Images](https://images.google.com.sg/)**
   Google Images. The most comprehensive image search on the web.

5. **[Gmail - Google](https://www.google.com.nf/webhp?hl=en&tab=ii)**
   Search the world's information, including webpages, images, videos and more. Google has many special features to help you find exactly what you're looking for.

### 查询: get Google Custom Search Engine ID programmable search

1. **[Programmable Search Engine ID - Google Help](https://support.google.com/programmable-search/answer/12499034?hl=en)**
   From the list of search engines, select the search engine for which you want to find the search engine ID. The Search engine ID is in the Basic section or in the jumped out...The Custom Search JSON API lets you develop websites and applications to …Help people find what they need on your website. Add a customizable search box …Programmable Search Engine enables you to create a search engine for your website, …

2. **[Search Engine ID and Google API Key - Coda](https://coda.io/@jon-dallas/google-image-search-pack-example/search-engine-id-and-google-api-key-3)**
   After creating a PSE, you will receive a unique Search Engine ID. This ID is used to specify which search engine to query. To access and integrate your Programmable Search Engine with …

3. **[Custom Search JSON API | Programmable Search Engine | Google …](https://developers.google.com/custom-search/v1/overview)**
   

4. **[How to Create Google Custom Search [Programmable Search …](https://geekflare.com/guide/create-google-custom-search/)**
   Mar 18, 2025 · You can use Google CSE (Programmable Search Engine) to create custom search experiences for your website users or consolidated search for internal teams. In this post, I’ll …

5. **[How to Get Google API Key & Custom Search Engine ID (Step-by …](/videos/riverview/relatedvideo?q=get+Google+Custom+Search+Engine+ID+programmable+search&ru=/search?q=get+Google+Custom+Search+Engine+ID+programmable+search&mmscn=vwrc&mid=ECFCDABE2D4523EA4118ECFCDABE2D4523EA4118&FORM=WRVORC&ntb=1&msockid=21ea54d7a5da11f0a34ce56e50ea2270)**
   Apr 20, 2025 · Learn how to easily get your Google API Key and set up a Custom Search Engine ID (CX) for your projects.

### 查询: Google CSE API credentials setup guide

1. **[Setting up API keys - API Console Help](https://support.google.com/googleapi/answer/6158862?hl=en)**
   To create your application's API key: Go to the API Console. From the projects list, select a project or create a new one. If the APIs & services page isn't already open, open the left side...

2. **[REST Resource: users.settings.cse.identities | Gmail | Google for ...](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.settings.cse.identities)**
   Jun 12, 2025 · The client-side encryption (CSE) configuration for the email address of an authenticated user. Gmail uses CSE configurations to save drafts of client-side encrypted email …

3. **[Client-side encryption setup overview - Google Help](https://support.google.com/a/answer/14309952?hl=en)**
   Before you start setting up Google Workspace Client-side encryption (CSE), review the requirements, encryption key options, and setup overview. CSE requirements

4. **[Manage API keys | Authentication | Google Cloud](https://cloud.google.com/docs/authentication/api-keys)**
   1 day ago · When you use the Google Cloud console to access Google Cloud services and APIs, you don't need to set up authentication. In the Google Cloud console, activate Cloud Shell. At the …

5. **[Create access credentials | Google Workspace | Google for Developers](https://developers.google.com/workspace/guides/create-credentials)**
   Aug 28, 2025 · Credentials are used to obtain an access token from Google's authorization servers so your app can call Google Workspace APIs. This guide describes how to choose and set up the...


---

## 详细教程内容

### 教程 1: https://geekflare.com/guide/create-google-custom-search/

Skip to content⟨1⟩
Google Custom Search Platform (CSE) is an excellent way to create a customizable search engine with all of Google’s search core capabilities.
You can use Google CSE (Programmable Search Engine) to create custom search experiences for your website users or consolidated search for internal teams.
In this post, I’ll cover Google Custom Search in detail, including what it is, a step-by-step guide to create one, and use cases.
## What is a Programmable Search Engine?
Google’s Programmable Search Engine’s core purpose is to allow website owners to include search engines on their websites.
For example, brands can create search engines to provide results from their own site or a subset of related sites.
Google CSE is equally helpful for individual users as they can create custom search engines to filter out content or focus on a particular set of resources.
![How to Create Google Custom Search \[Programmable Search Engine\] visual selection](data:image/svg+xml,%3Csvg%20xmlns='http://www.w3.org/2000/svg'%20width='601'%20height='626'%20viewBox='0%200%20601%20626'%3E%3C/svg%3E)
This custom search engine helps visitors find accurate information as it uses Google’s search technology, offering features such as autocomplete.
Plus, it’s completely customizable with a focus on the brand’s look and feel!
That’s why at Geekflare, we use Google CSE to power the site’s search capabilities.
> We, at Geekflare, use Google CSE for consolidated search across all websites. It is handy in day-to-day publishing operations and much better than the default WordPress search.
> Chandan Kumar, Founder, Geekflare
Even though it is aimed at businesses, anyone can create a custom search engine for their personal use.
Furthermore, you can link your custom search engine to Google Analytics to learn about the user’s behavior⟨2⟩.
I found the Programmable Search Engine to be great for different use cases. 
For example, a Reddit user created his own custom search engine to filter out specific programming resources such as W3Schools, Quora, and GeeksforGeeks.
> I just discovered Google’s “Programmable Search Engine.” I created my own custom search engine to filter out quora, w3schools, geeksforgreeks, etc!⟨3⟩ byu/premepopulation⟨4⟩ inprogramming⟨5⟩
The key benefits of using a Programmable Search Engine include:
  * Get relevant, high-quality search engine results
  * Showcase it on your site free of cost, or pay a low price for an ad-free experience
  * Customize in terms of looks and functionality
  * Use advanced controls like Ranking Priority and filtered elements

![Benefits of Google CSE⟨6⟩]
## Step-by-Step Guide to Create Custom Search Engine
Creating a Programmable Search Engine is easy. All you need to do is follow the steps mentioned below.
1. Go to the Programmable Search Engine⟨7⟩ site.
2. Click on “**Get started** ”.
![Google search engine get started⟨8⟩]
  1. Sign in to your Google account.
  2. Now, click the “**Add** ” button or “**Create your first searc

...(内容已截断)...


---

### 教程 2: https://cloud.google.com/docs/authentication/api-keys

 Skip to main content ⟨1⟩
 ![Google Cloud⟨2⟩ ](https://cloud.google.com/docs/authentication/</>)
`/`
  * English
  * Deutsch
  * Español
  * Español – América Latina
  * Français
  * Indonesia
  * Italiano
  * Português
  * Português – Brasil
  * 中文 – 简体
  * 中文 – 繁體
  * 日本語
  * 한국어

 Console ⟨3⟩ Sign in
  *  Google Cloud SDK ⟨4⟩


Contact Us⟨5⟩ Start free⟨6⟩
  *  Home ⟨7⟩
  *  Documentation ⟨8⟩
  *  Application development ⟨9⟩
  *  Google Cloud SDK ⟨4⟩
  *  Authentication ⟨10⟩
  *  Guides ⟨11⟩


Send feedback 
#  Manage API keys
Stay organized with collections  Save and categorize content based on your preferences. 
This page describes how to create, edit, and restrict API keys. For information about how to use API keys to access Google APIs, see Use API keys to access APIs⟨12⟩.
## Introduction to API keys
There are two types of API keys: standard API keys, and API keys that have been bound to a service account.
### Standard API keys
Standard API keys provide a way to associate a request with a project for billing and quota purposes. When you use a standard API key (an API key that has not been bound to a service account) to access an API, the API key doesn't identify a principal⟨13⟩. Without a principal, the request can't use Identity and Access Management (IAM) to check whether the caller is authorized to perform the requested operation.
Standard API keys can be used with any API that accepts API keys, unless API restrictions have been added to the key. Standard API keys can't be used with services that don't accept API keys, including in express mode⟨14⟩.
### API keys bound to a service account
API keys bound to a service account provide the identity and authorization of the service account to a request. When you use an API key that has been bound to a service account to access an API, your request is processed as if you used the bound service account to make the request.
The only API that supports bound API keys is `aiplatform.googleapis.com`.
Binding keys to a service account is prevented by a default organization policy constraint. To change this, see **Enable key binding to service accounts**⟨15⟩.
### API key components
An API key has the following components, which let you manage and use the key:
String
    The API key string is an encrypted string, for example, `AIzaSyDaGmWKa4JsXZ-HjGw7ISLn_3namBGewQe`. When you use an API key to access an API, you always use the key's string. API keys don't have an associated JSON file.
ID
    The API key ID is used by Google Cloud administrative tools to uniquely identify the key. The key ID can't be used to access APIs. The key ID can be found in the URL of the key's edit page in the Google Cloud console. You can also get the key ID by using the Google Cloud CLI to list the keys in your project.
Display name
    The display name is an optional, descriptive name for the key, which you can set when you create or update the key.
Bound service account
    API keys that are bound to a service account inclu

...(内容已截断)...


---

### 教程 3: https://developers.google.com/workspace/guides/create-credentials

 Skip to main content ⟨1⟩
 ![Google Workspace⟨2⟩ ](https://developers.google.com/workspace/guides/<https:/developers.google.com/workspace>)
  *  Google Workspace ⟨3⟩


`/`
  * English
  * Deutsch
  * Español
  * Español – América Latina
  * Français
  * Indonesia
  * Italiano
  * Polski
  * Português – Brasil
  * Tiếng Việt
  * Türkçe
  * Русский
  * עברית
  * العربيّة
  * فارسی
  * हिंदी
  * বাংলা
  * ภาษาไทย
  * 中文 – 简体
  * 中文 – 繁體
  * 日本語
  * 한국어

Sign in
Join us for Google Workspace Developer Summit on October 8th and 9th in Sunnyvale, CA⟨4⟩ and October 21st and 22nd in Paris, France⟨5⟩. Register today to connect with other developers and get a preview of the latest features and updates. 
  *  Home ⟨6⟩
  *  Google Workspace ⟨3⟩
  *  Guides ⟨7⟩


Send feedback 
#  Create access credentials
Stay organized with collections  Save and categorize content based on your preferences. 
![Spark icon⟨8⟩]
## AI-generated Key Takeaways
outlined_flag
  * Google Workspace APIs require credentials, which can be API keys, OAuth client IDs, or service accounts, depending on the type of access needed.
  * API keys provide anonymous access to public data and are created in the Google Cloud console.
  * OAuth client IDs are used for accessing user data with consent and require separate IDs for different platforms.
  * Service accounts enable applications to access data or act on behalf of users and require role assignment and secure key management.
  * Creating a service account involves assigning roles, generating keys, and optionally configuring domain-wide delegation for accessing user data on behalf of the application.


Credentials are used to obtain an access token from Google's authorization servers so your app can call Google Workspace APIs. This guide describes how to choose and set up the credentials your app needs.
For definitions of terms found on this page, see Authentication and authorization overview⟨9⟩.
## Choose the access credential that is right for you
The required credentials depends on the type of data, platform, and access methodology of your app. There are three types of credential types available:
Use case | Authentication method | About this authentication method  
---|---|---  
Access publicly available data anonymously in your app. | API keys⟨10⟩ | Check that the API that you want to use supports API keys before using this authentication method.  
Access user data such as their email address or age. | OAuth client ID⟨11⟩ | Requires your app to request and receive consent from the user.  
Access data that belongs to your own application or access resources on behalf of Google Workspace or Cloud Identity users through domain-wide delegation.⟨12⟩ | Service account⟨13⟩ | When an app authenticates as a service account, it has access to all resources that the service account has permission to access.  
### API key credentials
An API key is a long string containing upper and lower case letters, numbers, underscores, and hyphens, such as `AIz

...(内容已截断)...


---

## 快速步骤总结

根据搜索结果，获取 Google Custom Search API 的一般步骤如下：

### 获取 API Key:

1. 访问 [Google Cloud Console](https://console.cloud.google.com/)
2. 创建新项目或选择现有项目
3. 启用 Custom Search API
4. 转到 **APIs & Services** > **Credentials**
5. 点击 **Create Credentials** > **API Key**
6. 复制生成的 API Key

### 获取 CSE ID (Custom Search Engine ID):

1. 访问 [Google Programmable Search Engine](https://programmablesearchengine.google.com/)
2. 点击 **Get Started** 或 **New Search Engine**
3. 配置搜索引擎:
   - 指定要搜索的网站（或选择搜索整个网络）
   - 设置语言和地区
   - 给搜索引擎命名
4. 创建后，进入搜索引擎的控制面板
5. 在 **Setup** 或 **Overview** 页面找到 **Search engine ID (cx)**
6. 复制这个 ID，这就是您的 CSE ID

### 配置 Crawl4AI MCP Server:

编辑 `config.json` 文件:

```json
{
  "google": {
    "api_key": "your-api-key-here",
    "cse_id": "your-cse-id-here"
  }
}
```

### 注意事项:

- API Key 需要妥善保管，不要泄露
- 免费版 Custom Search API 每天有配额限制（通常是 100 次查询/天）
- 如需更多查询次数，需要设置计费账户
- CSE 可以配置为搜索特定网站或整个互联网
