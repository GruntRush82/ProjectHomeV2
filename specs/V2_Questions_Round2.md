# Project Home V2 — Questions Round 2 (Post-Plan)

> These questions dig into implementation details that the phased plan surfaced but doesn't fully resolve.
> Mission-related achievements have been removed. Missions now independently reward money + a unique flashy profile icon.

---

## Visual Design & Identity

**1. App branding** — Should V2 keep the name "Family Hub" or rebrand? The login screen and nav bar will show this name prominently. Any preference? ("Project Home"? "Home Base"? "The Hub"? Keep "Family Hub"?)
Let's call it "Felker Family Hub"

**2. Starter icon style** — The plan calls for 20 starter profile icons (before any are unlocked). What style appeals to your kids? Options: cartoon animals, emoji-style faces, space/sci-fi themed, gaming avatars, or a mix? This sets the visual tone.
The frist 20 should be plain but the other one should be much flashier and the more difficult to get the more flashy.

**3. Mission reward icons** — Completing a mission now grants a unique, flashy profile icon (separate from achievements). How flashy are we talking? Ideas: animated glow/pulse, gold/diamond border, particle effects on hover, or all of the above? Should each mission have a completely unique icon design (e.g., multiplication = a lightning brain, piano = golden music note)?
All of the above, mission icons should be really good.

**4. Light vs dark mode** — V1 uses a light theme with colorful accents. Should V2 stick with light, go dark (more "gaming" feel), or offer a toggle? Dark mode could be an unlockable achievement itself.

The UX should be completely redisgned. I would like a more modern feel, I want the kids to feel like this is a BIG upgrade. Dark is fine but last time it was difficult to see so be wary of contrast.

---

## Login & Session

**5. Idle timeout UX** — When the 5-minute idle timeout triggers, should it: (a) immediately snap back to the login screen, or (b) show a "Still there?" overlay with a 10-second countdown before reverting? The countdown gives someone actively using the app a chance to stay.
just snap back.
**6. User order on login screen** — Should the user icons on the login screen be in a fixed order (e.g., alphabetical, or a custom order you define), or should the last-used user be highlighted/first?
Just in order of creation.
---

## Calendar

**7. Calendar event deletion** — Can users delete calendar events they created in the app? And if it was pushed to Google Calendar, should the app also delete it from Google?
yes.
**8. Calendar visual layout** — The daily view will show Google Calendar events and chores. Should these be in two separate sections ("Events" and "Chores"), or interleaved into one chronological timeline? Chores don't have specific times, so interleaving gets tricky.
separated
**9. Chore time-of-day** — Should chores have an optional time-of-day (e.g., "Take out trash - 7:00 AM") so they can appear in the calendar timeline? Or are chores always just "sometime today"?
no anytime is fine.
---

## Chores

**10. Chore page scope** — When a user views their chore page, should it show the full 7-day week grid (like V1 but filtered to them), or just today + upcoming days? The calendar already handles "today."
The chore page can look very similar to V1 just with the new UX and limited to the user.
**11. XP for chores** — Should completing individual chores give XP? (The plan suggests +10 XP per chore.) This is small but adds up and gives the kids a reason to check things off promptly. Or should XP only come from bigger milestones (weekly 100%, streaks, missions)?
10 per chore is fine with a 2x bonus if you get 100% levels shoudl be increasingly difficult so 100 for level 2 250 for level 3 some scaling that makes sense.
---

## Bank

**12. Bank page layout** — The bank page has a lot: cash balance, savings, deposits timeline, interest ticker, weekly report, transaction ledger, savings goal, stats. Should this be: (a) one long scrollable page with sections, (b) a tabbed layout within the bank page (e.g., tabs for "Overview," "Savings," "History"), or (c) a dashboard grid layout?
History can be on a tab but the rest should be on a single page.
**13. Interest ticker visibility** — Should the real-time interest ticker only appear on the bank page, or should a small version be visible in the nav bar at all times (so kids see money growing wherever they are in the app)?
oooh good idea. I like it always being visible a lot!
**14. Savings deposit minimum** — Should there be a minimum savings deposit amount? (e.g., minimum $1.00 to avoid kids spamming $0.01 deposits that clutter the deposit tracker)
sure that makes sense.
**15. Cashout minimum** — Should there be a minimum cashout amount? Or can they cash out any amount, even $0.05?
sure $1 here too.
**16. Savings chunk visualization** — Each deposit has its own lock timer and needs a visual representation. Ideas: (a) stacked horizontal bars with countdown timers, (b) a timeline with blocks that "unlock" visually as time passes, (c) a vault-style grid where each deposit is a "box" that opens when unlocked. Which direction feels most fun?
keep thinking on this. I like the stacked bars, but is there a visual to make it more fun?!
**17. Cashout confirmation** — Before cashing out, should there be a confirmation step? ("You're about to cash out $42.50. This will send an email and reset your cash to $0. Proceed?") Or just let them click and go?
confirm is good.
**18. Interest on unlocked savings** — Once a savings deposit's lock period expires (but it hasn't been withdrawn yet), should it continue earning interest? Or does interest only accrue on locked deposits?
yes. it still earns interest after unlocked.
**19. Weekly report detail** — The bank page will show last week's performance. Should users be able to scroll back through previous weeks' reports, or just see the most recent one?
just last week is fine. 
**20. Savings withdrawal flow** — When a savings deposit unlocks and the user withdraws it, should the money: (a) go back to their cash account (so they can then cash out), or (b) go directly to cashout (email sent immediately, money leaves the system)? The current plan says (b) but want to confirm — going to cash first gives them the option to re-deposit into savings.
directly cash out. The users cash out maximum should be their cash account total + unlocked savings. Cash is always drawn first. The total should be displayed prominantly.
---

## Missions

**21. Mission icon showcase** — When a user completes a mission and earns their unique flashy icon, should it automatically become their active profile icon? Or should they get to choose when/if to equip it?
Yes it should it should be displayed lagely for a minute in the middle of the screen before changing their pic. There shoudl be much fanfare associated fire works and cheering. 

**22. Piano mission verification** — For the piano mission, should an admin need to confirm/approve completion? Or is the kid's self-report sufficient? An admin approval step adds accountability but also friction.
yes admin approval
**23. Mission training session length** — For multiplication training, how many problems per session feels right? 20? 30? Should the kid be able to choose (quick 10-problem session vs full 30-problem workout)?
let them chose.
**24. Mission progress visibility** — Should other family members be able to see that someone is working on a mission (without details)? E.g., "Calvin is training for Multiplication Master!" on the login screen. Or keep it fully private?
nah
**25. Future mission types** — Beyond multiplication and piano, any other ideas you're considering? Typing speed? Reading challenge? Physical fitness? Knowing even 1-2 more helps ensure the framework is flexible enough.
These all sound good. Lets start with these two and then develop more later. 
---

## Achievements & Gamification

**26. Achievement notification style** — When an achievement is unlocked, how should it appear? Options: (a) small toast notification in the corner, (b) full-screen celebration with animation and sound, (c) a banner that slides down and stays for a few seconds. Different tiers could get different treatments (small achievements = toast, big ones = full-screen).
yeah i like all three depending on the size of the achievement.

**27. Level-up visual impact** — The plan mentions levels affect profile visuals (border style, name glow). Should the entire app feel different at higher levels? For example: Level 1 = basic theme, Level 5 = subtle particle effects in the background, Level 10 = premium animated theme. Or keep level impact limited to the profile page?
I love it.

**28. Achievement difficulty curve** — Looking at the achievement list, are the thresholds reasonable? For example, is a 90-day streak realistic for your kids, or should the max be 30 days? Should "max out savings" be achievable within a few weeks, or be a long-term goal?
I think we can work on these achievements a bit, but I don't think they should unlock icons. Taht should be done from missions (mission speicific icons) or from XP. Acheivements can be a great way to get XP and there should also be able to see what achievements you have and which ones your dont yet. Your level should also be present on the login screen. Higher levels have better icons with cooler effects that can be seen on the login page. 

---

## Admin & Operations

**29. Admin config editing** — Should the admin dashboard let you edit ALL config values in a UI (interest rate, savings max, lock period, PIN, idle timeout), or should some stay as config-file-only to prevent accidental changes? If the kids can access admin by tapping Dad's icon, editable config in the UI means they could theoretically change their own interest rate.
everything in the ui is fine.
**30. Database backup** — Should the app automatically back up the SQLite database on a schedule (e.g., daily copy to a second location on the droplet, or even push to a cloud bucket)? This is cheap insurance against data loss. Or is manual backup sufficient?
yeah i like that idea.

