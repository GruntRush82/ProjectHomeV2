# Phase 4: Missions — Questions Before Implementation

These questions cover gaps and ambiguities in the current Phase 4 plan. Answers will be added to DECISIONS.md before implementation begins.

---
*Missions should only be available to the user that the admin assigns*

### Multiplication Mission — Training UX

**1. Training UI layout — how should the drill screen look?**
Should it be a simple centered question with a number pad (iPad-friendly, big tap targets), or more of a flashcard/game-style layout? Should there be a visible timer per question, or just track time silently in the background?

It should defnitely be ipad friendly. There should be a training option and a final test option. The final test should be random 12 times table questions and to pass you need to get 45 in 60 seconds. The training should have a silent confidence phase that drills questions that she has gotten good at. and an explore phase that attempts to teach new questions.

**2. Adaptive weighting — how aggressive should it be?**
The plan says to weight toward weak facts. Should it be a gentle bias (e.g., 2x more likely to see a weak fact) or heavily weighted (e.g., 50% of questions are from the weakest facts)? And how many sessions of data should it use for weighting — all history, or just the last N sessions?
last 3 sessions. gentle bias.

**3. Should training show the correct answer immediately on a wrong answer?**
When the kid gets one wrong, should it flash the correct answer before moving on? Or just mark it wrong and show a summary at the end?
No, encouraging message and then another attempt. if the child gets it wrong again give the answer and maybe a fun numonic device to help remember that answer. Assume that the tactic is memorization not deduction.

**4. Training session feedback — what does the end-of-session screen show?**
Score and percentage are obvious. Should it also show: time per question, a list of missed facts, a comparison to previous sessions, a "facts mastered" count, or a motivational message?

Up to you but be motivational. Try and show progress.

**5. Can kids retake training sessions freely, or is there any cooldown/daily limit?**
Unlimited training could mean grinding for hours. Should there be a soft nudge ("Great work! Take a break and come back later") or a hard daily cap?

No I really doubt this will be an issue lol.
---

### Multiplication Mission — Testing

**6. During the 60-second test, what's the input method?**
Should kids type the answer with a number pad on screen, use the iPad keyboard, or tap from multiple-choice options? Number pad is probably fastest for a timed test, but want to confirm.

numpad

**7. What happens visually during the test?**
Should there be a prominent countdown timer? A running score? Or is it intentionally minimal to reduce anxiety (just the question and input, with a small timer)?

no timers or scores on training.

**8. After a failed test, what feedback is given?**
Just the score ("You got 28/35")? A comparison to the target? Which questions were missed? An encouraging message? Should it show how close they were to passing?

yes be encouraging. The test shouldn't end after 60 seconds, but a completion within 60 seconds is required. ACTUALLY. lets do levels! level 1 test has no time limit and just requires 45 correct answers. this unlocks level 2 which requires 45 correct answers in 120 seconds. This unlocks level 3 which requires 45 correct answers in 60 seconds and unlocks the cash, xp, and custom mission profile pic.

**9. Is there a cooldown between test attempts, or can they retry immediately?**
After failing, can they jump right back into a test, or should they be required to do at least one more training session first (back to `training` state)?

no cooldown.

---

### Piano Mission

**10. How specific should the piano mission be — one hardcoded piece, or configurable per assignment?**
The plan shows "Fur Elise" as an example. Should each piano mission assignment specify the piece name and description in its config, so you could assign different pieces to different kids?

The kid can put the name of the peice in.


**11. What does the piano mission training phase actually look like in the app?**
Since the app can't listen to piano playing, is training just a log/journal ("I practiced today" button with optional minutes)? Or is it purely honor-system with no in-app training tracking — just the state transitions (start practicing -> I'm ready -> admin approves)?

no training in the paino one its super easy just an admin confirmed completion nothing to do for training or testing.

**12. When the kid clicks "I'm ready to perform," does anything happen before admin review?**
Should there be a confirmation ("Are you sure you're ready? Your parent will need to watch you play"), or does it just flip to `pending_approval` immediately?

There should just be a I did it button, which flips it to pending approval.
---

### Mission Framework & Admin

**13. Where does mission creation and assignment happen — admin dashboard (Phase 6) or a temporary UI now?**
The admin dashboard is Phase 6, but missions need to be assigned in Phase 4. Should we build a minimal admin missions page now, or seed missions via a script/API and build the full admin UI later?

mission creation has to happen under the hood in the code base. But the assignment of missions should happen from the admin page. once the app is in prod, the next phase will be to create many new missions, these will require updates but the mission archtecture should assume that we will be creating many new missionsin the furutre.

**14. Can a user have multiple active missions at once?**
For example, could Calvin be working on multiplication AND piano at the same time? Or is it one mission at a time per user?

yes

**15. Can the same mission type be assigned to multiple kids simultaneously?**
E.g., can both Calvin and Lilah each have their own multiplication mission running independently?

yes
---

### Rewards & Celebration

**16. How much cash reward for each mission?**
The plan says `reward_cash` is configurable per mission. Do you have specific amounts in mind for multiplication and piano? (e.g., $5, $10, $25?)
admin defined.

**17. The 60-second celebration with the icon displayed center-screen — is that literally 60 seconds?**
That's a long time to stare at a screen. Should it be shorter (15-20 seconds) with a "dismiss" button, or do you genuinely want a full minute of glory?
haha no i don't know where this came from, my mistake. No definitely not a minute of glory, but the new profile pic and the cash reward should feature prominatntly in the celebration screen.

**18. Should the mission reward cash deposit appear as a transaction in the bank?**
The Transaction model already has `TYPE_MISSION_REWARD`. Should completing a mission auto-deposit the cash reward into the kid's bank account with a transaction record, or is it handled differently?

no that's fine.

---

### Missions Page UX

**19. What does the missions hub page (`/missions`) look like when there are no active missions?**
Should it show an empty state like "No missions assigned yet — ask a parent!" or should it also show completed missions / available mission types?

sure.

**20. Should there be any notification or visual indicator on the nav bar when a mission is assigned or when a kid becomes "ready for test"?**
For example, a badge/dot on the Missions nav icon, or a toast notification when they log in?

I like the idea of a new mission assigned notification when the admin assigns the mission to a user on the next login.
