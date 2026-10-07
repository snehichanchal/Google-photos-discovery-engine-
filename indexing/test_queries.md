# Retrieval Quality Test Report

This report contains the top 3 results from both the Dense Vector Index (ChromaDB) and Sparse Keyword Index (BM25) for a set of 10 test queries.

## Query 1: `I want to find a picture of my dog but the search doesn't work`

### Dense Search (ChromaDB)
1. **Distance**: 0.3901 | **Source**: HackerNews Social
   > (Part 2/2) I enter "black dog" it shows pictures with black color somewhere in the picture, like a shadow, and a dog. If I enter "dog with black hair"...
2. **Distance**: 0.4286 | **Source**: HackerNews Social
   > Smartphone buyers meh on AI, care more about battery life Don't use the name - "Mr Floppy at the beach" is meaningless, but "dog at a beach" will prob...
3. **Distance**: 0.4359 | **Source**: Google Play Store (2/5)
   > Ongoing issue for some time now. It fails to recognise pets in a lot of photos. If I type in search bar "dogs", those pet photos appear, however if I ...

### Sparse Search (BM25)
1. **Score**: 25.1828 | **Source**: HackerNews Social
   > (Part 2/2) I enter "black dog" it shows pictures with black color somewhere in the picture, like a shadow, and a dog. If I enter "dog with black hair"...
2. **Score**: 22.2089 | **Source**: HackerNews Social
   > (Part 1/2) On Not Carrying a Camera – Cultivating memories instead of snapshots I have at least 140k digital photos (almost 30 years of digital camera...
3. **Score**: 19.0504 | **Source**: Google Play Store (2/5)
   > This app is practically unusable anymore. The search engine doesn't ever freaking work when trying to find a specific photo, Even on Wi-Fi the page lo...

---

## Query 2: `App crashes when I try to scroll through old photos from years ago`

### Dense Search (ChromaDB)
1. **Distance**: 0.3126 | **Source**: Google Play Store (1/5)
   > The photos aren't lost, they are 6 yr old photos that are present in the Google Photos Cloud. I restored them to a phone so I may edit them and use th...
2. **Distance**: 0.3228 | **Source**: Apple App Store (1/5)
   > You Broke it What did you do?  I used this every week for 10+ years but in the past 2-3 months it became unusable.   Photos will not delete inside the...
3. **Distance**: 0.3522 | **Source**: Apple App Store (2/5)
   > Can’t scroll down when searching in Photos I like to look back on my photos, and find the search function helpful to do this, by searching for a date ...

### Sparse Search (BM25)
1. **Score**: 20.0438 | **Source**: Apple App Store (2/5)
   > Can’t scroll down when searching in Photos I like to look back on my photos, and find the search function helpful to do this, by searching for a date ...
2. **Score**: 19.3268 | **Source**: Apple App Store (1/5)
   > Crashes when saving photos back to phone Decided use Amazon photo instead of Google as it has unlimited storage for photos. It was very annoying when ...
3. **Score**: 18.6356 | **Source**: Apple App Store (3/5)
   > Photos jumping back to the start Hi! When I try to load more photos, ie. scroll down into the next month or search in an album- the app tries to load ...

---

## Query 3: `How can I search for text inside a screenshot?`

### Dense Search (ChromaDB)
1. **Distance**: 0.4849 | **Source**: HackerNews Social
   > Ask HN: Notes, mind-maps, browser tabs all in one solution? You’re definitely looking for DEVONThink[1] if you haven’t seen it yet. Based on the descr...
2. **Distance**: 0.5159 | **Source**: YouTube
   > Search by Image How do you do it on a phone?...
3. **Distance**: 0.5302 | **Source**: HackerNews Social
   > Ask HN: Is there open source AI based search engine for photos? I have my own photos on computers. 1000s of them. On google photos, I can find a photo...

### Sparse Search (BM25)
1. **Score**: 13.4902 | **Source**: Google Photos Help Community
   > When I check a screenshot I have sent by clicking on it. I see a line of previous screenshots at the When I send a screenshot to another party and che...
2. **Score**: 12.8039 | **Source**: Reddit
   > Whenever I take a photo and try to edit it right away, I get an error message when I try to upload it anywhere. I've been dealing with this for a few ...
3. **Score**: 11.9836 | **Source**: HackerNews Social
   > (Part 3/5) account. The most interesting feature, in my opinion - Popup menus. It’s something like Edit Menus on iOS or Contextual Menus on Android bu...

---

## Query 4: `Lost my vacation album from last summer`

### Dense Search (ChromaDB)
1. **Distance**: 0.5307 | **Source**: Reddit
   > Devastated -- all my photos and albums gone. I am absolutely devastated, I had been backing up photos to Google photos and even paying for extra stora...
2. **Distance**: 0.5732 | **Source**: Apple App Store (1/5)
   > Update play all my albums Just downloaded the latest version and all my albums have disappeared. I can still see them via a browser but not on the app...
3. **Distance**: 0.5825 | **Source**: Google Play Store (1/5)
   > the app is great, but I lost almost most of my photos and I have no idea how. im trying to get them but im not very positive. I was just trying to del...

### Sparse Search (BM25)
1. **Score**: 14.9609 | **Source**: YouTube
   > I Moved to Immich… Can It Really Replace Google Photos? Immich would be great if it functioned with folders rather than unnestable albums. I don't sca...
2. **Score**: 10.1113 | **Source**: Apple App Store (2/5)
   > Issue motion/live photos in album Adding live/motion photos to the album makes the photo static. Live/motions photos are lost when added to a shared a...
3. **Score**: 7.4815 | **Source**: Google Play Store (3/5)
   > This app is great but something isn't working with the backup, albums and syncing across devices/platforms at the moment. I created an album on anothe...

---

## Query 5: `Facial recognition is grouping two different people together`

### Dense Search (ChromaDB)
1. **Distance**: 0.4736 | **Source**: Apple App Store (1/5)
   > Matching problem Matches different people to each other...
2. **Distance**: 0.4888 | **Source**: HackerNews Social
   > Texas sues Google for collecting biometric data without consent First of all, "biometric data" is a scary-sounding term that sounds like iris or finge...
3. **Distance**: 0.5106 | **Source**: Reddit
   > Edit users(persons) on photos The app automatically regroup photos with same faces into a person. I had like 5 persons and each time I added a photo i...

### Sparse Search (BM25)
1. **Score**: 12.7284 | **Source**: Reddit
   > facial recognition problem Hey guys, Need some help with a weird Google Photos issue. I switched to a new Google account about 2 weeks ago. Face group...
2. **Score**: 12.2425 | **Source**: YouTube
   > I Moved to Immich… Can It Really Replace Google Photos? I wish Immich had a way to share facial recognition information between user accounts....
3. **Score**: 11.6276 | **Source**: Google Play Store (3/5)
   > With the last update or couple, the facial recognition got SO bad. It used to be pretty good, recognizing faces 80% or so of the time. Now within ten ...

---

## Query 6: `Can't find downloaded images, they disappear from the gallery`

### Dense Search (ChromaDB)
1. **Distance**: 0.3492 | **Source**: Google Play Store (3/5)
   > u know its a good app and i actually i work so much with it , it helps me a lot , but recently when i download some pictures , and i wanna find it in ...
2. **Distance**: 0.3731 | **Source**: Reddit
   > Can't Archive Specific Set of Photos I have a specific set of photos that won't go away. I've checked to see if my device was auto downloading them fr...
3. **Distance**: 0.3753 | **Source**: Reddit
   > CAMERA ROLL PHOTOS NOT SHOWING IN GALLERY Samsung Note 10+ – Photos not showing in Gallery My camera photos and screenshots suddenly stopped showing i...

### Sparse Search (BM25)
1. **Score**: 18.2167 | **Source**: Google Play Store (1/5)
   > Please give people a choice of how they want their photos laid out. The random choice of big photos influenced behind the scenes w/ai that I didn't as...
2. **Score**: 16.0403 | **Source**: Google Play Store (1/5)
   > Can't sort "on this device" folders at all, photos are sometimes duplicated in photos view, can't move images between folders, folder backup randomly ...
3. **Score**: 13.9168 | **Source**: Google Play Store (4/5)
   > The app keeps removing my downloaded photos from backup. they'll be there for a week or so then disappear. I've turned off all the freeing up space se...

---

## Query 7: `Sorting by date is broken, pictures show up in the wrong year`

### Dense Search (ChromaDB)
1. **Distance**: 0.3468 | **Source**: YouTube
   > Google Photos: Complete 2025 Guide (Hidden Features You're Missing) I just replaced my 8 yr old android phone with a new android phone. My old phone j...
2. **Distance**: 0.3815 | **Source**: Google Play Store (1/5)
   > Using Google Android Pixel with updated app (as I do not believe others with iPhones have this bug): I have many Google Photos albums and sort by "new...
3. **Distance**: 0.3965 | **Source**: Google Play Store (4/5)
   > I really love this google app but.. have this new actualization and now all the photos are all together. Im sorry but i don't like that, i prefer the ...

### Sparse Search (BM25)
1. **Score**: 17.5109 | **Source**: Google Play Store (2/5)
   > I used to really like this app but things have gotten so confusing that it's nearly impossible to find pictures. I don't understand why sometimes pict...
2. **Score**: 15.5995 | **Source**: Google Play Store (3/5)
   > new layout is absolutely horrible. I wish I could revert to old UI. random pictures are randomly larger than others when viewing the photos page. I ca...
3. **Score**: 14.0960 | **Source**: Google Play Store (3/5)
   > I like this app, but I can't change file names and I have been experiencing glitches with typed descriptions as a whole. Update 6/6/26- Some of my pic...

---

## Query 8: `Is there a way to filter videos only without photos?`

### Dense Search (ChromaDB)
1. **Distance**: 0.4989 | **Source**: HackerNews Social
   > On Not Carrying a Camera I went the other way around. I carry my Z8 everywhere (in the backpack or on the strap), take it with me when I travel anywhe...
2. **Distance**: 0.5086 | **Source**: Google Play Store (1/5)
   > Their photo-to-video filter is excessively strict. My wife and I tried a photo of us together and it was blocked. Yes we were fully clothed. We disabl...
3. **Distance**: 0.5246 | **Source**: Google Play Store (4/5)
   > This is my favorite way to keep my photos and videos backed up period but I wish that there was a way to set photos and videos to only be saved if the...

### Sparse Search (BM25)
1. **Score**: 18.8277 | **Source**: Google Play Store (4/5)
   > This is my favorite way to keep my photos and videos backed up period but I wish that there was a way to set photos and videos to only be saved if the...
2. **Score**: 16.3766 | **Source**: Apple App Store (1/5)
   > i’m going to find a different way to save my memories without limits and without trashy edits. I don't want my memories to have music with lyrics. I a...
3. **Score**: 16.0724 | **Source**: HackerNews Social
   > Show HN: We built an end-to-end encrypted alternative to Google Photos Thanks for the detailed responses! Some more questions: a) I note the pricing i...

---

## Query 9: `Need to recover deleted photos from trash but it's empty`

### Dense Search (ChromaDB)
1. **Distance**: 0.2410 | **Source**: Google Photos Help Community
   > Recover deleted photos from trash I need to recover deleted photos from trash...
2. **Distance**: 0.2584 | **Source**: Google Photos Help Community
   > Picture delete photos from trash I want to recovery me delete photos and videos from trash history kindly recover my soom as picture...
3. **Distance**: 0.2690 | **Source**: Google Photos Help Community
   > Want to recover last 4 days deleted photos from trash I really want to restore a screenshot that I deleted from the trash as it contained a very impor...

### Sparse Search (BM25)
1. **Score**: 28.5702 | **Source**: Google Photos Help Community
   > Recover deleted photos from trash I need to recover deleted photos from trash...
2. **Score**: 22.1398 | **Source**: Google Photos Help Community
   > Restore deleted photos from trash I want to restore my deleted photos from trash history Kindly recover my dataz as soon as possible.....
3. **Score**: 22.0135 | **Source**: Google Photos Help Community
   > Restore deleted photos from trash I want to restore my deleted photos & videos from trash history Kindly recover my dataz as soon as p…...

---

## Query 10: `Cannot upload high quality images anymore`

### Dense Search (ChromaDB)
1. **Distance**: 0.4891 | **Source**: Apple App Store (1/5)
   > Fail to upload I cant upload all my photos to this app. Even on app or website. Google keep fail me to upload my photos because i dont wanna to automa...
2. **Distance**: 0.5114 | **Source**: Google Photos Help Community
   > I upload video on Google photos but this is very slow and I can't upload too many video.... please It takes over 10 minutes to upload 100 mb size of v...
3. **Distance**: 0.5144 | **Source**: Reddit
   > Anyone having issues changing backup quality from Original to Storage Saver? I just wiped and refreshed my old Pixel 3a and now I cannot change the qu...

### Sparse Search (BM25)
1. **Score**: 12.6329 | **Source**: HackerNews Social
   > Apple Stole My Music I keep my RAW images on OneDrive for backup and use Google Photos with the free version / high quality version. I find Google Pho...
2. **Score**: 10.5816 | **Source**: Reddit
   > Anyone having issues changing backup quality from Original to Storage Saver? I just wiped and refreshed my old Pixel 3a and now I cannot change the qu...
3. **Score**: 10.3335 | **Source**: HackerNews Social
   > Show HN: We built an end-to-end encrypted alternative to Google Photos Thanks for the detailed responses! Some more questions: a) I note the pricing i...

---
