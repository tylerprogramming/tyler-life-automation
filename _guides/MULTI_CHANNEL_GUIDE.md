# 📺 Multi-Channel YouTube Analysis Guide

This guide explains how to use the new multi-channel YouTube video analysis functionality that allows you to analyze multiple YouTube channels and get their latest videos from a specified time period.

## 🚀 **Overview**

The multi-channel analysis system allows you to:
- ✅ Analyze multiple YouTube channels simultaneously
- ✅ Get videos from the last X days/weeks (default: 2 weeks)
- ✅ Support various YouTube URL formats
- ✅ Filter videos by publish date
- ✅ Get comprehensive video data (views, likes, comments, duration)
- ✅ Handle errors gracefully for invalid channels

## 🔧 **API Endpoints**

### 1. **POST /youtube/multi-channel/analyze** (Recommended)

Analyze multiple channels with a JSON request body.

**Request:**
```bash
curl -X POST http://localhost:8000/youtube/multi-channel/analyze \
     -H "Content-Type: application/json" \
     -d '{
       "channel_urls": [
         "https://www.youtube.com/@MrBeast",
         "https://www.youtube.com/@mkbhd",
         "https://www.youtube.com/channel/UCuAXFkgsw1L7xaCfnd5JJOw"
       ],
       "days_back": 14,
       "max_videos_per_channel": 20
     }'
```

**Parameters:**
- `channel_urls` (required): List of YouTube channel URLs
- `days_back` (optional): Number of days to look back (default: 14, range: 1-365)
- `max_videos_per_channel` (optional): Max videos per channel (default: 50, range: 1-100)

### 2. **GET /youtube/multi-channel/analyze**

Alternative GET version using query parameters.

**Request:**
```bash
curl "http://localhost:8000/youtube/multi-channel/analyze?channel_urls=https://www.youtube.com/@MrBeast&channel_urls=https://www.youtube.com/@mkbhd&days_back=7&max_videos_per_channel=10"
```

### 3. **GET /youtube/channel/extract-id**

Test channel ID extraction from URLs.

**Request:**
```bash
curl "http://localhost:8000/youtube/channel/extract-id?url=https://www.youtube.com/@MrBeast"
```

## 🔗 **Supported URL Formats**

The system supports various YouTube URL formats:

| Format | Example | Description |
|--------|---------|-------------|
| Direct Channel ID | `https://www.youtube.com/channel/UCuAXFkgsw1L7xaCfnd5JJOw` | Direct channel ID URL |
| @Username | `https://www.youtube.com/@MrBeast` | New @username format |
| Legacy User | `https://www.youtube.com/user/GoogleDevelopers` | Legacy /user/ format |
| Custom Channel | `https://www.youtube.com/c/TED` | Custom channel URL |
| Short Format | `youtube.com/channelname` | Simplified format |

## 📊 **Response Format**

The API returns a comprehensive analysis with this structure:

```json
{
  "channels": [
    {
      "url": "https://www.youtube.com/@MrBeast",
      "channel_id": "UCX6OQ3DkcsbYNE6H8uQQuVA",
      "channel_name": "MrBeast",
      "subscriber_count": 200000000,
      "video_count": 5,
      "videos": [
        {
          "video_id": "xyz123",
          "title": "Video Title",
          "description": "Video description...",
          "published_at": "2024-01-15T10:00:00Z",
          "thumbnail": "https://img.youtube.com/vi/xyz123/medium.jpg",
          "duration": "PT10M30S",
          "view_count": 1000000,
          "like_count": 50000,
          "comment_count": 2500,
          "video_url": "https://www.youtube.com/watch?v=xyz123",
          "tags": ["tag1", "tag2"],
          "category_id": "22"
        }
      ],
      "error": null
    }
  ],
  "total_videos": 15,
  "date_range": {
    "from": "2024-01-01T00:00:00",
    "to": "2024-01-15T00:00:00",
    "days_back": 14
  },
  "summary": {
    "channels_processed": 3,
    "channels_successful": 2,
    "channels_failed": 1,
    "total_videos_found": 15
  }
}
```

## 🎯 **Use Cases**

### 1. **Competitor Analysis**
Monitor what your competitors are posting:
```bash
curl -X POST http://localhost:8000/youtube/multi-channel/analyze \
     -H "Content-Type: application/json" \
     -d '{
       "channel_urls": [
         "https://www.youtube.com/@competitor1",
         "https://www.youtube.com/@competitor2"
       ],
       "days_back": 7,
       "max_videos_per_channel": 30
     }'
```

### 2. **Content Research**
Find trending content in your niche:
```bash
curl -X POST http://localhost:8000/youtube/multi-channel/analyze \
     -H "Content-Type: application/json" \
     -d '{
       "channel_urls": [
         "https://www.youtube.com/@TechChannel1",
         "https://www.youtube.com/@TechChannel2",
         "https://www.youtube.com/@TechChannel3"
       ],
       "days_back": 30,
       "max_videos_per_channel": 50
     }'
```

### 3. **Weekly Content Roundup**
Get weekly updates from favorite channels:
```bash
curl -X POST http://localhost:8000/youtube/multi-channel/analyze \
     -H "Content-Type: application/json" \
     -d '{
       "channel_urls": [
         "https://www.youtube.com/@News1",
         "https://www.youtube.com/@News2"
       ],
       "days_back": 7,
       "max_videos_per_channel": 20
     }'
```

## 🧪 **Testing**

Test the functionality with our test script:

```bash
cd tyler-skool-members
python3 test_multi_channel_analysis.py
```

This will test:
- URL parsing for various formats
- Single channel video retrieval
- Multi-channel analysis
- Date filtering
- API endpoint functionality

## 📈 **Data Analysis Tips**

### **Video Performance Metrics**
- **View Count**: Raw popularity indicator
- **Like Count**: Engagement quality
- **Comment Count**: Discussion level
- **Duration**: Content length analysis
- **Publish Date**: Timing patterns

### **Channel Comparison**
- **Subscriber Count**: Channel size
- **Video Count**: Publishing frequency
- **Average Views**: Performance per video
- **Content Categories**: Topic focus

### **Trend Analysis**
- **Daily/Weekly Patterns**: When channels post
- **Content Themes**: Popular topics via tags
- **Performance Correlation**: Views vs. duration, timing, etc.

## ⚡ **Performance Considerations**

### **API Quotas**
- YouTube Data API has daily quotas
- Each channel analysis uses multiple API calls
- Consider reducing `max_videos_per_channel` for many channels

### **Rate Limiting**
- The system handles API rate limits automatically
- Large requests may take longer to process
- Consider breaking up very large analyses

### **Optimization Tips**
- Use shorter `days_back` periods for faster results
- Limit `max_videos_per_channel` to essential videos
- Cache results if analyzing the same channels repeatedly

## 🛠 **Error Handling**

The system gracefully handles various errors:

### **Invalid URLs**
```json
{
  "url": "https://invalid-url.com",
  "error": "Could not extract channel ID from URL"
}
```

### **Channels Not Found**
```json
{
  "url": "https://www.youtube.com/@nonexistent",
  "error": "Channel not found: UCxxxxxxxxx"
}
```

### **API Errors**
```json
{
  "url": "https://www.youtube.com/@channel",
  "error": "Error processing channel: API quota exceeded"
}
```

## 🔧 **Troubleshooting**

### **No Videos Found**
- Check if the channel has posted in the specified date range
- Increase `days_back` parameter
- Verify the channel URL is correct

### **API Errors**
- Ensure YouTube Data API is enabled in Google Cloud Console
- Check your API key has sufficient quota
- Verify your API key is valid

### **Slow Performance**
- Reduce `max_videos_per_channel`
- Use shorter `days_back` periods
- Analyze fewer channels per request

## 🚀 **Integration Examples**

### **Python Integration**
```python
import requests

def analyze_competitors(channel_urls, days=14):
    response = requests.post(
        "http://localhost:8000/youtube/multi-channel/analyze",
        json={
            "channel_urls": channel_urls,
            "days_back": days,
            "max_videos_per_channel": 25
        }
    )
    return response.json()

# Usage
channels = [
    "https://www.youtube.com/@competitor1",
    "https://www.youtube.com/@competitor2"
]
results = analyze_competitors(channels, days=7)
print(f"Found {results['total_videos']} videos")
```

### **JavaScript Integration**
```javascript
async function analyzeChannels(channelUrls, daysBack = 14) {
    const response = await fetch('/youtube/multi-channel/analyze', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            channel_urls: channelUrls,
            days_back: daysBack,
            max_videos_per_channel: 25
        })
    });
    
    return await response.json();
}

// Usage
const channels = [
    'https://www.youtube.com/@competitor1',
    'https://www.youtube.com/@competitor2'
];

analyzeChannels(channels, 7)
    .then(results => {
        console.log(`Found ${results.total_videos} videos`);
    });
```

## 🎉 **Success!**

You now have a powerful multi-channel YouTube analysis system that can:
- 📊 Analyze competitor content strategies
- 🔍 Research trending topics in your niche  
- 📈 Track publishing patterns and performance
- 🎯 Identify content opportunities
- 📅 Monitor recent activities across multiple channels

The system is designed to be flexible, reliable, and easy to integrate into your existing workflows! 🚀 