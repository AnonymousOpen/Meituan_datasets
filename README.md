# Meituan datasets for STAGE

Meituan:https://about.meituan.com/en is one of the largest O2O (online-to-offline) local life service platforms connecting more than 240 million consumers and various local services, such as entertainment, dining, delivery, travel, etc.
We conduct experiments on two real-world user consumption session datasets collected from Meituan in two cities of China, i.e., Beijing and Shanghai, from Jan. 1st, 2021 to Jan. 8th, 2021. Following the definition of spatiotemporal context on Meituan business, there are 13 location scenes and 96 time-slots (dividing a day into 48 time-slots at half-hour intervals and distinguishing weekends and weekdays).
**The location is the relative location scenes (13 types) that defined by Meituan according to its business scenarios, which have been verified to be more suitable than the absolute latitude and longitude information in the Meituan platform.**

**Data format：userID   sessionID   itemID   timestamp   timeID   locationID**
