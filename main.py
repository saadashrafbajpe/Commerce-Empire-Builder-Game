# commerce_builder_gui_pretty.py
# A prettier Tkinter UI for Commerce Builder
# - Uses ttk themes, colored frames, emoji icons, and progress bars for Capital & Reputation
# - Keeps original game logic, events, hard=10 rounds, and scoring out of 1000

import random
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, scrolledtext

# ---------------- Game logic (unchanged core, slightly refactored) ----------------
def profit_boost(state, low_perc, high_perc):
    perc = random.uniform(low_perc, high_perc)
    bonus = state['capital'] * perc * 0.1
    state['capital'] += bonus
    return bonus

def cost_hit(state, low, high):
    cost = random.uniform(low, high)
    cost = min(cost, state['capital'])
    state['capital'] -= cost
    return -cost

def cost_hit_and_rep(state, low, high, rep_low, rep_high):
    cost = random.uniform(low, high)
    cost = min(cost, state['capital'])
    state['capital'] -= cost
    rep_change = random.randint(rep_low, rep_high)
    state['reputation'] = max(0, state['reputation'] + rep_change)
    return -cost

def profit_and_rep_boost(state, low_perc, high_perc, rep_low, rep_high):
    perc = random.uniform(low_perc, high_perc)
    bonus = max(50, state['capital'] * perc * 0.1)
    state['capital'] += bonus
    rep_change = random.randint(rep_low, rep_high)
    state['reputation'] = min(100, state['reputation'] + rep_change)
    return bonus

def rep_and_revenue_hit(state, rep_low, rep_high, rev_low_pct, rev_high_pct):
    rep_change = -random.randint(rep_low, rep_high)
    state['reputation'] = max(0, state['reputation'] + rep_change)
    penalty = random.uniform(rev_low_pct, rev_high_pct)
    state['last_revenue_penalty'] = penalty
    return 0

def revenue_penalty(state, low_pct, high_pct):
    penalty = random.uniform(low_pct, high_pct)
    state['last_revenue_penalty'] = penalty
    return 0

def rep_boost(state, low, high):
    change = random.randint(low, high)
    state['reputation'] = min(100, state['reputation'] + change)
    return 0

def rep_hit(state, low, high):
    change = random.randint(low, high)
    state['reputation'] = max(0, state['reputation'] - change)
    return 0

def clear_turn_modifiers(state):
    if 'last_revenue_penalty' in state:
        del state['last_revenue_penalty']

# Score out of 1000
def compute_score_out_of_1000(state):
    cap = float(state['capital'])
    tgt = float(state['target_capital']) if state.get('target_capital', 0) else 1.0
    ratio = cap / tgt
    ratio_clamped = max(0.0, min(ratio, 2.5))
    capital_score = ratio_clamped / 2.5 * 750.0
    rep = float(state.get('reputation', 50))
    reputation_score = (rep / 100.0) * 200.0
    branches = float(state.get('branches', 1))
    branch_factor = min(branches, 10.0) / 10.0
    branch_score = branch_factor * 150.0
    survival_score = 0.0
    if cap > 0:
        survival_score += 100.0
        start_cap = float(state.get('start_capital', cap))
        gain_ratio = (cap - start_cap) / max(1.0, start_cap)
        gain_clamped = max(-1.0, min(gain_ratio, 2.0))
        survival_score += max(0.0, gain_clamped) * 50.0
    raw = capital_score + reputation_score + branch_score + survival_score
    final = int(max(0, min(1000, round(raw))))
    return final

# Random events
def random_event(state):
    events = [
        ("Festival Season Boom", "Good",
         "Huge sales due to festival season! Extra profit flows in.",
         lambda s: profit_boost(s, 0.4, 0.9)),
        ("Rent Hike", "Bad",
         "Landlord increases rent on all branches significantly.",
         lambda s: cost_hit(s, 400, 1200)),
        ("Tax Inspection", "Bad",
         "Surprise tax inspection! You pay a fine and paperwork slows you down.",
         lambda s: cost_hit_and_rep(s, 200, 800, -5, 0)),
        ("Viral Marketing", "Good",
         "Your brand goes viral on social media. Reputation and short sales spike!",
         lambda s: profit_and_rep_boost(s, 0.15, 0.4, 5, 20)),
        ("Customer Complaint", "Bad",
         "A complaint spreads online. Reputation takes a hit and short-term sales drop.",
         lambda s: rep_and_revenue_hit(s, 5, 20, 0.05, 0.25)),
        ("Supply Chain Delay", "Bad",
         "A supplier delay increases costs and reduces revenue this turn.",
         lambda s: cost_hit(s, 150, 500) or revenue_penalty(s, 0.05, 0.25)),
        ("Local Festival Collab", "Good",
         "Local event partners want to collaborate — modest gains and reputation boost.",
         lambda s: profit_boost(s, 0.1, 0.3) or rep_boost(s, 3, 8)),
        ("Competitor Discount", "Bad",
         "A competitor runs a heavy discount campaign — your revenue suffers.",
         lambda s: revenue_penalty(s, 0.1, 0.35)),
        ("Nothing Special", "Neutral",
         "A normal business day. No surprises.",
         lambda s: 0),
    ]
    ev = random.choice(events)
    title, mood, desc, effect_fn = ev
    delta = effect_fn(state)
    return title, mood, desc, delta

# ---------------- UI: Pretty Tkinter with ttk ----------------
class PrettyCommerce:
    def __init__(self, root):
        self.root = root
        root.title("Commerce Builder — Pretty Edition")
        root.geometry('1000x650')
        root.minsize(900,600)

        # ttk theme and styles
        style = ttk.Style(root)
        # Use default theme, but configure custom colors
        try:
            style.theme_use('clam')
        except Exception:
            pass

        style.configure('TFrame', background='#0b1220')
        style.configure('Header.TLabel', font=('Segoe UI', 18, 'bold'), foreground='#e6f2ff', background='#06202b')
        style.configure('Stat.TLabel', font=('Segoe UI', 11), foreground='#f0f8ff', background='#0b1220')
        style.configure('Accent.TButton', font=('Segoe UI', 10, 'bold'), foreground='#042f2e')
        style.map('Accent.TButton', background=[('!disabled','#34d399'), ('active', '#10b981')])
        style.configure('Danger.TButton', font=('Segoe UI', 10, 'bold'), foreground='white', background='#ef4444')
        style.map('Danger.TButton', background=[('!disabled','#ef4444'), ('active', '#dc2626')])

        # Top header
        header = ttk.Frame(root, style='TFrame', padding=(12,10))
        header.pack(fill='x')
        title = ttk.Label(header, text='💼 COMMERCE BUILDER', style='Header.TLabel')
        title.pack(side='left')

        # Info bar (capital, rep, branches, turn)
        info_bar = ttk.Frame(root, style='TFrame', padding=(10,8))
        info_bar.pack(fill='x')
        self.cap_var = tk.DoubleVar(value=0.0)
        self.rep_var = tk.DoubleVar(value=50.0)

        # Capital progress (styled)
        cap_frame = ttk.Frame(info_bar, style='TFrame')
        cap_frame.pack(side='left', padx=10)
        ttk.Label(cap_frame, text='💰 Capital', style='Stat.TLabel').pack(anchor='w')
        self.cap_bar = ttk.Progressbar(cap_frame, orient='horizontal', length=300, mode='determinate', maximum=20000, variable=self.cap_var)
        self.cap_bar.pack()
        self.cap_label = ttk.Label(cap_frame, text='₹0.00', style='Stat.TLabel')
        self.cap_label.pack(anchor='e')

        # Reputation progress
        rep_frame = ttk.Frame(info_bar, style='TFrame')
        rep_frame.pack(side='left', padx=10)
        ttk.Label(rep_frame, text='⭐ Reputation', style='Stat.TLabel').pack(anchor='w')
        self.rep_bar = ttk.Progressbar(rep_frame, orient='horizontal', length=200, mode='determinate', maximum=100, variable=self.rep_var)
        self.rep_bar.pack()
        self.rep_label = ttk.Label(rep_frame, text='50 / 100', style='Stat.TLabel')
        self.rep_label.pack(anchor='e')

        # Branches and Turn quick stats
        misc_frame = ttk.Frame(info_bar, style='TFrame')
        misc_frame.pack(side='right', padx=12)
        self.branches_var = tk.IntVar(value=1)
        self.turn_var = tk.IntVar(value=1)
        ttk.Label(misc_frame, text='🏬 Branches: ', style='Stat.TLabel').grid(row=0, column=0, sticky='e')
        self.branches_label = ttk.Label(misc_frame, textvariable=self.branches_var, style='Stat.TLabel')
        self.branches_label.grid(row=0, column=1, sticky='w')
        ttk.Label(misc_frame, text='🔁 Turn: ', style='Stat.TLabel').grid(row=1, column=0, sticky='e')
        self.turn_label = ttk.Label(misc_frame, textvariable=self.turn_var, style='Stat.TLabel')
        self.turn_label.grid(row=1, column=1, sticky='w')

        # Main area: buttons (left) and history (right)
        main = ttk.Frame(root, style='TFrame', padding=12)
        main.pack(fill='both', expand=True)

        left = ttk.Frame(main, style='TFrame')
        left.pack(side='left', fill='y', padx=(0,12))

        ttk.Label(left, text='Make a choice', style='Stat.TLabel').pack(anchor='w')

        # Buttons with emoji icons
        self.btn_open = ttk.Button(left, text='🏗️ Open New Branch (₹1500)', style='Accent.TButton', command=lambda: self.take_turn('1'))
        self.btn_open.pack(fill='x', pady=6)
        self.btn_marketing = ttk.Button(left, text='📣 Marketing (₹600)', style='Accent.TButton', command=lambda: self.take_turn('2'))
        self.btn_marketing.pack(fill='x', pady=6)
        self.btn_cut = ttk.Button(left, text='✂️ Cut Expenses (₹200)', style='Accent.TButton', command=lambda: self.take_turn('3'))
        self.btn_cut.pack(fill='x', pady=6)
        self.btn_safe = ttk.Button(left, text='🛡️ Play Safe', style='Accent.TButton', command=lambda: self.take_turn('4'))
        self.btn_safe.pack(fill='x', pady=6)

        ttk.Separator(left, orient='horizontal').pack(fill='x', pady=8)
        ttk.Button(left, text='🔚 End Game Now', style='Danger.TButton', command=self.end_game_now).pack(fill='x', pady=6)
        ttk.Button(left, text='🔄 Restart', command=self.start_new_game).pack(fill='x', pady=6)

        # Right: history log with styled header and small stats
        right = ttk.Frame(main, style='TFrame')
        right.pack(side='right', fill='both', expand=True)

        header2 = ttk.Frame(right, style='TFrame')
        header2.pack(fill='x')
        ttk.Label(header2, text='📜 Turn History', style=('Stat.TLabel')).pack(anchor='w')

        self.txt = scrolledtext.ScrolledText(right, wrap='word', state='disabled', height=20, background='#07121a', foreground='#dbeafe')
        self.txt.pack(fill='both', expand=True)

        # Footer: score / tips area
        footer = ttk.Frame(root, style='TFrame', padding=10)
        footer.pack(fill='x')
        self.tips_label = ttk.Label(footer, text='Tip: Invest in marketing for reputation; cut costs for short-term relief.', style='Stat.TLabel')
        self.tips_label.pack(side='left')
        self.score_label = ttk.Label(footer, text='Score: -- / 1000', style='Stat.TLabel')
        self.score_label.pack(side='right')

        # Initialize game state
        self.state = None
        self.start_new_game()

    def append(self, text):
        self.txt.configure(state='normal')
        self.txt.insert('end', text + '\n')
        self.txt.see('end')
        self.txt.configure(state='disabled')

    def refresh_dashboard(self):
        st = self.state
        # progressbar ranges: capital bar maximum is 20000 by default; update as needed
        self.cap_var.set(min(20000, max(0, st['capital'])))
        self.cap_label.config(text=f'₹{st["capital"]:.2f}')
        self.rep_var.set(max(0, min(100, st['reputation'])))
        self.rep_label.config(text=f"{st['reputation']} / 100")
        self.branches_var.set(st['branches'])
        self.turn_var.set(st['turn'] if st['turn'] <= st['max_turns'] else st['max_turns'])

    def start_new_game(self):
        # Prompt for name & difficulty using simpledialog
        name = simpledialog.askstring('Business Name', 'Enter your business name:', initialvalue='Dream Ventures')
        if name is None:
            return
        diff = None
        while diff not in ('1','2','3'):
            diff = simpledialog.askstring('Difficulty', 'Choose difficulty:\n1 - Easy (₹8000, 8 turns, target ₹12000)\n2 - Normal (₹6000, 7 turns, target ₹10000)\n3 - Hard (₹5000, 10 turns, target ₹12000)\nEnter 1, 2 or 3:', initialvalue='2')
            if diff is None:
                return
        if diff == '1':
            capital, max_turns, target = 8000, 8, 12000
        elif diff == '2':
            capital, max_turns, target = 6000, 7, 10000
        else:
            capital, max_turns, target = 5000, 10, 12000

        self.state = {
            'name': name,
            'capital': float(capital),
            'start_capital': float(capital),
            'branches': 1,
            'reputation': 50,
            'turn': 1,
            'max_turns': max_turns,
            'target_capital': target
        }
        self.txt.configure(state='normal')
        self.txt.delete('1.0', 'end')
        self.txt.configure(state='disabled')
        self.append(f'🎬 New Game: {name} | Difficulty: {"Easy" if diff=="1" else "Normal" if diff=="2" else "Hard"}')
        self.refresh_dashboard()
        self.score_label.config(text='Score: -- / 1000')

    def take_turn(self, choice):
        st = self.state
        if not st:
            messagebox.showinfo('No game', 'Start a new game first.')
            return
        if st['turn'] > st['max_turns'] or st['capital'] <= 0:
            messagebox.showinfo('Game Over', 'Game already finished — start a new one.')
            return

        base_rent_per_branch = 400
        tax_rate = 0.12

        action_cost = 0
        rent = base_rent_per_branch * st['branches']
        revenue_base = 800 + st['branches'] * 300
        rep_factor = 0.5 + (st['reputation'] / 200.0)
        revenue = revenue_base * rep_factor * random.uniform(0.8, 1.3)

        revenue_pen = st.get('last_revenue_penalty', 0)
        if revenue_pen:
            revenue *= (1 - revenue_pen)

        self.append(f'\n🔁 TURN {st["turn"]} — Choice: {choice}')

        if choice == '1':
            cost_new_branch = 1500
            if st['capital'] >= cost_new_branch:
                st['branches'] += 1
                action_cost += cost_new_branch
                self.append('🏗️ Opened a new branch (₹1500)')
                roll = random.random()
                if roll < 0.15:
                    overrun = random.uniform(200, 600)
                    st['capital'] -= overrun
                    st['reputation'] = max(0, st['reputation'] - random.randint(1,4))
                    self.append(f'⚠️ Construction overrun: -₹{overrun:.2f}, reputation decreased')
                elif roll > 0.85:
                    bonus = random.uniform(200, 800)
                    st['capital'] += bonus
                    self.append(f'✨ New branch launch success: +₹{bonus:.2f}')
            else:
                self.append('❌ Not enough capital to open a new branch!')
        elif choice == '2':
            marketing_cost = 600
            if st['capital'] >= marketing_cost:
                action_cost += marketing_cost
                rep_gain = random.randint(5, 15)
                st['reputation'] = min(100, st['reputation'] + rep_gain)
                self.append(f'📣 Marketing: Reputation +{rep_gain} (cost ₹600)')
                roll = random.random()
                if roll < 0.12:
                    rep_loss = random.randint(5, 12)
                    penalty = random.uniform(100, 400)
                    st['reputation'] = max(0, st['reputation'] - rep_loss)
                    st['capital'] -= min(st['capital'], penalty)
                    self.append(f'🔥 Ad backlash: Reputation -{rep_loss}, paid ₹{penalty:.2f}')
                elif roll > 0.82:
                    viral_gain = random.uniform(400, 1200)
                    st['capital'] += viral_gain
                    self.append(f'🚀 Campaign went viral: +₹{viral_gain:.2f}')
            else:
                self.append('❌ Not enough capital for marketing campaign!')
        elif choice == '3':
            cut_cost = 200
            if st['capital'] >= cut_cost:
                action_cost += cut_cost
                rent *= 0.5
                self.append('✂️ Cut expenses: Rent halved this turn (cost ₹200)')
                if random.random() < 0.3:
                    rep_loss = random.randint(1,6)
                    st['reputation'] = max(0, st['reputation'] - rep_loss)
                    self.append(f'😕 Staff morale hit: Reputation -{rep_loss}')
                else:
                    st['next_efficiency_bonus'] = st.get('next_efficiency_bonus', 0) + random.uniform(50, 200)
                    self.append('⚙️ Efficiency improvements queued for next turn')
            else:
                self.append('❌ Not enough capital to optimize expenses!')
        elif choice == '4':
            self.append('🛡️ Played safe this turn')
            st['safe_play'] = True

        gross_profit = revenue - rent - action_cost
        eff_bonus = st.pop('next_efficiency_bonus', 0)
        if eff_bonus:
            gross_profit += eff_bonus
            self.append(f'💡 Efficiency bonus applied: +₹{eff_bonus:.2f}')

        tax = 0
        if gross_profit > 0:
            tax = gross_profit * tax_rate
        net_profit = gross_profit - tax

        st['capital'] += net_profit

        # Display turn financials
        self.append(f'📊 Revenue: ₹{revenue:.2f} | Rent: ₹{rent:.2f} | Action: ₹{action_cost:.2f} | Tax: ₹{tax:.2f}')
        if net_profit >= 0:
            self.append(f'✅ Net Profit: ₹{net_profit:.2f}')
        else:
            self.append(f'❌ Net Loss: ₹{abs(net_profit):.2f}')

        # Random event handling (safe_play reduces chance of bad outcome)
        if st.pop('safe_play', False):
            if random.random() < 0.45:
                self.append('🟢 Conservative approach avoided surprises this turn')
            else:
                title, mood, desc, delta = random_event(st)
                self.append(f'🎲 EVENT — {title} ({mood}): {desc}')
        else:
            title, mood, desc, delta = random_event(st)
            self.append(f'🎲 EVENT — {title} ({mood}): {desc}')
            if isinstance(delta, (int, float)) and delta != 0:
                if delta > 0:
                    self.append(f'Impact: +₹{delta:.2f}')
                else:
                    self.append(f'Impact: -₹{abs(delta):.2f}')

        clear_turn_modifiers(st)
        st['turn'] += 1
        self.refresh_dashboard()

        # End check
        if st['turn'] > st['max_turns'] or st['capital'] <= 0:
            self.finish_game()

    def finish_game(self):
        st = self.state
        score = compute_score_out_of_1000(st)
        self.score_label.config(text=f'Score: {score} / 1000')
        summary = f"GAME OVER — {st['name']}\nFinal Capital: ₹{st['capital']:.2f}\nBranches: {st['branches']}\nReputation: {st['reputation']}\nTurns Played: {st['turn']-1}\nScore: {score} / 1000"
        messagebox.showinfo('Game Over', summary)
        self.append('\n=== GAME OVER ===')
        self.append(summary)
        st['turn'] = st['max_turns'] + 1

    def end_game_now(self):
        if not self.state:
            return
        if messagebox.askyesno('End Game', 'End the game now?'):
            self.finish_game()

    def refresh_dashboard(self):
        st = self.state
        # Auto-scale capital progressbar max if you exceed current max
        current_cap = st['capital']
        max_cap = self.cap_bar['maximum']
        if current_cap > max_cap:
            # bump maximum smoothly
            new_max = max_cap
            while new_max < current_cap:
                new_max *= 1.5
            self.cap_bar.config(maximum=new_max)
        self.cap_var.set(max(0, st['capital']))
        self.cap_label.config(text=f'₹{st["capital"]:.2f}')
        self.rep_var.set(max(0, min(100, st['reputation'])))
        self.rep_label.config(text=f"{st['reputation']} / 100")
        self.branches_var.set(st['branches'])
        self.turn_var.set(st['turn'] if st['turn'] <= st['max_turns'] else st['max_turns'])

# ---------------- Run the app ----------------
if __name__ == '__main__':
    root = tk.Tk()
    app = PrettyCommerce(root)
    root.mainloop()
