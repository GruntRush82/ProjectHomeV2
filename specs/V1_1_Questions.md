# V1.1 Planning — Questions & Answers

> Round 1 Q&A before implementation begins.
> Please fill in answers below each question.

---

## Feature 1 — Today page & Weekly Calendar

**Q1.** The weekly Calendar page will show Google Calendar events. Should it also show local events created inside the app (e.g., "dentist appointment" added by a family member), or strictly events pulled from Gmail?

> A: yes for sure in fact ther eshould be no difference as events that are created in app should be pushed to the gmail calendar.

---

**Q2.** Should users be able to create new events from the weekly Calendar page, or is it read-only (view only)?

> A: yes they should be able to.

---

**Q3.** The nav bar currently has 6 items (Calendar → Today, Chores, Grocery, Bank, Missions, Profile). Adding a 7th "Calendar" item makes it 7. Is that fine for iPad, or would you prefer to drop or merge one of the existing items (e.g., fold Chores into Today, or remove Grocery from the nav)?

> A:no 7. Creating lifestyle goals should be done in the profile page, lifestyle points should be accrued in the bank, and redeeming points, view the previliges menu should be done in the bank. Tracking open privilages and viewing redemption history should be done in the profile page. 

---

**Q4.** The weekly Calendar shows "all 7 days with the month and date." Should it show events for all family members, or only the currently logged-in user's events?

> A: Events are not assigned to users. This should not be an option.

---

**Q5.** The Today page currently redirects to `/calendar` after login. After renaming to `/today`, should the default post-login redirect stay as the Today page, or change to something else?

> A:The default page should be the today page.

---

## Feature 2 — Bank allowance indicator

**Q6.** Should the allowance display also show the user's earning history (e.g., how much they actually earned last week vs. their potential), or just the fixed weekly allowance amount?

> A: sure history is cool.

---

**Q7.** Fire Mode currently shows the boosted allowance amount. Should the allowance display also show the Fire Mode bonus calculation when Fire Mode is active, or just always show the base allowance?

> A: should show the base amount.

---

## Feature 3 — Mission rewards

**Q8.** For the gem display on the Profile page — should a completed mission card appear even if the admin never assigned a gem type/size to it (showing a default "no gem" state), or should the section only appear once at least one completed mission has a gem assigned?

> A: The gem should just be like a sticker section. Missions should need a gem choice. also it would be cool to see tiny gems on the login page at the bottom of the card.

---

**Q9.** The existing two missions (Multiplication Master and Piano Performance) have no gem/description assigned yet. Should you be able to set those retroactively via the admin UI, or do you want to decide their gems now so I can hard-code them into the seed?

> A: Just remove the current missions and I will recreate them with the required selections.

---

**Q10.** Should the reward_description (free-form reward like "Hamster") appear anywhere other than the profile page? For example, in the mission completion celebration overlay, or in the admin overview, or just on the profile?

> A: yeah the mission page should include info about the xp reward and the monitary/string reward.

---

**Q11.** Should the reward preview on the missions page (showing gem + XP + description before the mission is completed) be visible to all users, or only to the assigned user?

> A:just the assigned.

---

**Q12.** The current XP reward for all missions is hardcoded at 500. Should this become configurable per-mission by the admin (like cash reward already is), or should it stay fixed at 500 across all missions?

> A: yes configurable

---

## Feature 4 — Lifestyle Points

**Q13.** When logging a goal, can a user log it multiple times in one day — e.g., "Read 30 min" logged twice counts as 2 toward a weekly target of 3 — or is it capped at 1 log per day per goal?

> A:no just binary daily. but the weekly tally should be visible in the today page. so if its thursday and the user has completed their "read" goal twice before the today page should indicate a weekly tally of 2, the goal of 4(or whatever it was set at), and an indicator of whether today has been done. when they click it for today it should count up the weekly tally, and if the tally reaches the goal there should be some indicator that you have succeeded like it should become green or something.

---

**Q14.** If a user creates a new goal mid-week (say Wednesday), does that week count toward their lifestyle point, or do they only start being evaluated from the following Monday?

> A:it can count right away. 

---

**Q15.** Can a user have goals that only apply on certain days (e.g., "Weight training" only Mon/Wed/Fri), or are all goals evaluated as a weekly count target with no specific day restrictions?

> A: no no restrictions.

---

**Q16.** Should the lifestyle points balance and privilege shop appear on the Bank page as well (alongside cash/savings), or only on the Today page?

> A: yes.

---

**Q17.** Should the admin be able to see each family member's lifestyle goal progress in the admin panel overview (e.g., "Calvin: 2/3 goals on track this week"), or is the admin only managing the privilege menu?

> A: no that's not necessary.

---

**Q18.** When a user redeems a privilege and it shows as "pending," can they cancel the redemption and get their points back, or is the redemption final once submitted?

> A: yes they can cancel.

---

**Q19.** Should lifestyle goals and the privilege shop be visible to everyone (all family members can see each other's goals and redemptions), or is it private per-user?

> A: per user.

---

## General

**Q20.** Are there any new achievements you'd want to add for the new features? For example: "Logged all lifestyle goals for a full week," "Redeemed first privilege," "Viewed the Calendar 7 days in a row"? Or should the achievement catalog stay as-is for now?

> A:yes please.

---
additional note: The admin should be able to undo completed missions if they were marked completed in error this should repeal the xp and money/reward and gems and achievements and could result in negative values if the money was cashed out. But it is possible that a mission which does not require a test was completed in error, or maybe an unauthorized user logs on a completes a tested mission. 


*Answers to these questions will be recorded in `specs/DECISIONS.md` before implementation begins.*
