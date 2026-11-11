import math, os
from PIL import Image, ImageDraw, ImageFont

W, H = 850, 480
RADIUS = 16

try:
    font_bold = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 13)
    font_med = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 12)
    font_small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 10)
    font_mono = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 11)
    font_mono_bold = ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', 13)
    font_title = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 14)
    font_banner = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 15)
except:
    font_bold = font_med = font_small = font_mono = font_mono_bold = font_title = font_banner = ImageFont.load_default()

def draw_window_frame(draw, active_tab=0):
    # Base dark container
    draw.rounded_rectangle([0, 0, W - 1, H - 1], radius=RADIUS, fill=(13, 17, 23, 255), outline=(48, 54, 61, 255), width=2)
    
    # Title bar
    draw.rounded_rectangle([0, 0, W - 1, 38], radius=RADIUS, fill=(22, 27, 34, 255))
    draw.rectangle([0, 18, W - 1, 38], fill=(22, 27, 34, 255))
    draw.line([(0, 38), (W, 38)], fill=(48, 54, 61, 255), width=1)
    
    # Traffic light dots
    draw.ellipse([16, 13, 26, 23], fill=(239, 68, 68, 255))
    draw.ellipse([34, 13, 44, 23], fill=(245, 158, 11, 255))
    draw.ellipse([52, 13, 62, 23], fill=(16, 185, 129, 255))
    
    # Navigation tabs in titlebar
    tabs = [
        "1. Section Controller Radar Console",
        "2. Station Concourse PIDS LED Board",
        "3. Passenger Mobile Tracking & BTS"
    ]
    tab_x = 90
    for i, t in enumerate(tabs):
        is_active = (i == active_tab)
        bg = (30, 41, 59, 255) if is_active else (22, 27, 34, 255)
        fg = (248, 250, 252, 255) if is_active else (148, 163, 184, 255)
        border = (59, 130, 246, 255) if is_active else (48, 54, 61, 255)
        
        bbox = draw.textbbox((0, 0), t, font=font_small)
        tw = bbox[2] - bbox[0] + 16
        draw.rounded_rectangle([tab_x, 8, tab_x + tw, 30], radius=5, fill=bg, outline=border, width=1)
        draw.text((tab_x + 8, 11), t, fill=fg, font=font_small)
        tab_x += tw + 10

def render_phase_1(frame_idx, total_p1_frames=30):
    """Control Room Radar & Dynamic 4-Aspect Signal Headway."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_window_frame(draw, active_tab=0)
    
    # Progress [0, 1]
    prog = frame_idx / float(total_p1_frames - 1)
    
    # Sub-header with Indian Railways Cultural Styling
    draw.rounded_rectangle([20, 44, 130, 68], radius=6, fill=(255, 199, 44, 255), outline=(217, 119, 6, 255), width=1)
    draw.text((28, 48), "CRIS RADAR", fill=(11, 15, 25, 255), font=font_bold)
    draw.text((145, 48), "SECTION CONTROLLER & RADAR DESK", fill=(241, 245, 249, 255), font=font_banner)
    draw.text((540, 50), "Division: NCR | GZB-CNB High-Density Corridor", fill=(148, 163, 184, 255), font=font_small)
    
    # Corridor Track Canvas (Dark Slate)
    draw.rounded_rectangle([20, 75, 570, 345], radius=10, fill=(15, 23, 42, 255), outline=(30, 41, 59, 255), width=2)
    draw.text((32, 85), "LIVE DOWNSTREAM TRACK OCCUPANCY & ABS BLOCK HEADWAY", fill=(56, 189, 248, 255), font=font_bold)
    
    # Railway Track Lines (Double Track)
    track_y = 200
    draw.line([(40, track_y - 2), (550, track_y - 2)], fill=(100, 116, 139, 255), width=3)
    draw.line([(40, track_y + 8), (550, track_y + 8)], fill=(100, 116, 139, 255), width=3)
    # Sleepers
    for sx in range(40, 550, 15):
        draw.line([(sx, track_y - 6), (sx, track_y + 12)], fill=(71, 85, 105, 255), width=2)
        
    # Stations along track
    stations = [(70, "GHAZIABAD [GZB]"), (230, "ALIGARH [ALJN]"), (390, "TUNDLA [TDL]"), (510, "KANPUR [CNB]")]
    for stx, stname in stations:
        draw.line([(stx, track_y - 18), (stx, track_y + 24)], fill=(148, 163, 184, 255), width=2)
        draw.circle((stx, track_y + 3), 4, fill=(59, 130, 246, 255))
        draw.text((stx - 25, track_y - 32), stname.split()[0], fill=(203, 213, 225, 255), font=font_small)
        
    # Train 12951 Position animating
    train_x = int(140 + prog * 160)
    draw.rounded_rectangle([train_x - 35, track_y - 14, train_x + 35, track_y + 20], radius=6, fill=(37, 99, 235, 255), outline=(96, 165, 250, 255), width=2)
    draw.text((train_x - 30, track_y - 10), "12951 RAJDHANI", fill=(255, 255, 255, 255), font=font_small)
    draw.text((train_x - 22, track_y + 4), f"{128 - int(prog * 8)} km/h", fill=(191, 219, 254, 255), font=font_small)
    
    # Preceding Freight Train
    freight_x = 420
    draw.rounded_rectangle([freight_x - 30, track_y - 14, freight_x + 30, track_y + 20], radius=6, fill=(180, 83, 9, 255), outline=(245, 158, 11, 255), width=2)
    draw.text((freight_x - 26, track_y - 10), "BOXN FREIGHT", fill=(255, 255, 255, 255), font=font_small)
    draw.text((freight_x - 18, track_y + 4), "45 km/h", fill=(254, 243, 199, 255), font=font_small)
    
    # Headway bracket
    headway_km = max(1.2, 4.5 - prog * 3.1)
    draw.line([(train_x + 37, track_y + 32), (freight_x - 32, track_y + 32)], fill=(234, 179, 8, 255), width=2)
    draw.text(((train_x + freight_x)//2 - 40, track_y + 38), f"Headway: {headway_km:.1f} km", fill=(250, 204, 21, 255), font=font_small)
    
    # Signal Aspect Post
    sig_x = train_x + 55
    draw.rounded_rectangle([sig_x, track_y - 65, sig_x + 18, track_y - 18], radius=4, fill=(30, 41, 59, 255), outline=(71, 85, 105, 255))
    draw.line([(sig_x + 9, track_y - 18), (sig_x + 9, track_y - 2)], fill=(100, 116, 139, 255), width=3)
    
    # 4-Aspect deduction
    if prog < 0.35:
        aspect_name = "GREEN [CLEAR - 130 km/h]"
        sig_color = (34, 197, 94, 255)
        draw.circle((sig_x + 9, track_y - 56), 4, fill=(34, 197, 94, 255))
    elif prog < 0.70:
        aspect_name = "DOUBLE YELLOW [ATTENTION - 80 km/h]"
        sig_color = (234, 179, 8, 255)
        draw.circle((sig_x + 9, track_y - 44), 4, fill=(234, 179, 8, 255))
        draw.circle((sig_x + 9, track_y - 32), 4, fill=(234, 179, 8, 255))
    else:
        aspect_name = "SINGLE YELLOW [CAUTION - 45 km/h]"
        sig_color = (249, 115, 22, 255)
        draw.circle((sig_x + 9, track_y - 44), 4, fill=(249, 115, 22, 255))
        
    draw.text((32, 290), f"Current ABS Signal Aspect: {aspect_name}", fill=sig_color, font=font_bold)
    draw.text((32, 312), f"Signal Penalty: +{(prog * 6.5):.1f} min | Section Delay: +{(11.0 + prog * 4.2):.1f} min", fill=(203, 213, 225, 255), font=font_small)
    
    # Right Telemetry Sidecar
    draw.rounded_rectangle([585, 75, 830, 345], radius=10, fill=(15, 23, 42, 255), outline=(30, 41, 59, 255), width=2)
    draw.text((597, 85), "LOCOMOTIVE & PHYSICS TELEMETRY", fill=(168, 85, 247, 255), font=font_bold)
    
    telem = [
        ("Loco Class", "WAP-7 (Electric 6000 HP)"),
        ("Tractive Effort", "325.0 kN (Continuous)"),
        ("Davis Resistance", f"{34.2 + prog * 4.5:.1f} kN [R=A+Bv+Cv^2]"),
        ("Weather Speed Cap", "Clear Sky (130 km/h MPS)"),
        ("Braking Distance", "840 m (Service Full)"),
        ("Section Slack", "14.0 min WTT Buffer")
    ]
    ty = 115
    for k, v in telem:
        draw.text((597, ty), k, fill=(148, 163, 184, 255), font=font_small)
        draw.text((705, ty), v, fill=(241, 245, 249, 255), font=font_small)
        ty += 22
        
    # Bottom Dispatch Advisory Strip
    if prog >= 0.50:
        draw.rounded_rectangle([20, 360, 830, 460], radius=8, fill=(16, 185, 129, 35), outline=(16, 185, 129, 255), width=2)
        draw.text((35, 372), "AI PRECEDENCE ADVISOR: LOOP LINE CLEARANCE RECOMMENDATION", fill=(52, 211, 153, 255), font=font_bold)
        draw.text((35, 396), "Action: Divert Preceding BOXN Freight to Loop Line at Tundla Jn (Platform Loop 2).", fill=(241, 245, 249, 255), font=font_med)
        draw.text((35, 422), f"Projected Net Delay Savings: +14.2 minutes for Rajdhani 12951 | Headway Clearance: 100% Green Restored", fill=(110, 231, 183, 255), font=font_small)
    else:
        draw.rounded_rectangle([20, 360, 830, 460], radius=8, fill=(30, 41, 59, 255), outline=(51, 65, 85, 255), width=1)
        draw.text((35, 372), "DOWNSTREAM SECTION HEALTH: NOMINAL SPATIAL FLOW", fill=(148, 163, 184, 255), font=font_bold)
        draw.text((35, 398), "Monitoring active rakes on Down Line. Headway buffer healthy. Quantile forecast: [P10: 17:02, P50: 17:08, P90: 17:15].", fill=(203, 213, 225, 255), font=font_med)

    return img

def render_phase_2(frame_idx, total_p2_frames=30):
    """Station Concourse PIDS LED Board & Platform Conflict Alert."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_window_frame(draw, active_tab=1)
    
    prog = frame_idx / float(total_p2_frames - 1)
    conflict_resolved = (prog >= 0.65)
    
    # Sub-header with Authentic IR Signboard Pill
    draw.rounded_rectangle([20, 44, 255, 68], radius=6, fill=(255, 199, 44, 255), outline=(217, 119, 6, 255), width=1)
    draw.text((28, 48), "NDLS • NEW DELHI JUNCTION", fill=(11, 15, 25, 255), font=font_bold)
    draw.text((270, 48), "CONCOURSE PIDS LED BOARD", fill=(241, 245, 249, 255), font=font_banner)
    draw.text((610, 50), "Dual-Clock STA vs Dynamic ETA", fill=(250, 204, 21, 255), font=font_small)
    
    # PIDS Display Board Table (High-contrast LED look)
    draw.rounded_rectangle([20, 75, 830, 345], radius=10, fill=(10, 15, 25, 255), outline=(59, 130, 246, 255), width=2)
    
    # Table Header
    headers = [
        (35, "TRAIN NUMBER & NAME"),
        (260, "ORIGIN -> DEST"),
        (420, "SCHEDULED (STA)"),
        (550, "DYNAMIC ETA (AI)"),
        (680, "DELAY STATUS"),
        (780, "PF")
    ]
    draw.rectangle([21, 76, 829, 105], fill=(30, 41, 59, 255))
    for hx, htitle in headers:
        draw.text((hx, 84), htitle, fill=(203, 213, 225, 255), font=font_bold)
        
    # Rows
    train_rows = [
        ("12951 RAJDHANI EXP", "NDLS -> BCT", "16:55", "17:08", "+13m (Physics Delay)", "PF 3", (239, 68, 68, 255)),
        ("12004 SHATABDI EXP", "NDLS -> LKO", "17:10", "17:12", "+2m (Near Normal)", "PF 5" if conflict_resolved else "PF 3*", (34, 197, 94, 255) if conflict_resolved else (245, 158, 11, 255)),
        ("22436 VANDE BHARAT", "NDLS -> BSB", "17:25", "17:25", "ON TIME (Optimal)", "PF 1", (34, 197, 94, 255)),
        ("12302 HOWRAH RAJDHANI", "NDLS -> HWH", "17:40", "17:43", "+3m (WTT Absorbed)", "PF 4", (34, 197, 94, 255)),
        ("12424 DBRG RAJDHANI", "NDLS -> DBRG", "18:00", "18:14", "+14m (Fog Cap 60km/h)", "PF 2", (239, 68, 68, 255))
    ]
    
    ry = 115
    for tr_name, od, sta, eta, status_text, pf, stat_col in train_rows:
        draw.line([(22, ry + 36), (828, ry + 36)], fill=(30, 41, 59, 255), width=1)
        draw.text((35, ry + 8), tr_name, fill=(255, 255, 255, 255), font=font_bold)
        draw.text((260, ry + 9), od, fill=(148, 163, 184, 255), font=font_small)
        draw.text((420, ry + 8), sta, fill=(241, 245, 249, 255), font=font_mono_bold)
        draw.text((550, ry + 8), eta, fill=(56, 189, 248, 255), font=font_mono_bold)
        draw.text((680, ry + 9), status_text, fill=stat_col, font=font_small)
        
        pf_bg = (16, 185, 129, 255) if pf == "PF 5" and conflict_resolved else ((239, 68, 68, 255) if "*" in pf else (37, 99, 235, 255))
        draw.rounded_rectangle([775, ry + 4, 820, ry + 28], radius=4, fill=pf_bg)
        draw.text((782, ry + 8), pf, fill=(255, 255, 255, 255), font=font_bold)
        
        ry += 42

    # Bottom Alert / Conflict Resolution Strip
    if not conflict_resolved:
        flash = (int(prog * 10) % 2 == 0)
        border_col = (239, 68, 68, 255) if flash else (245, 158, 11, 255)
        draw.rounded_rectangle([20, 360, 830, 460], radius=8, fill=(239, 68, 68, 30), outline=border_col, width=2)
        draw.text((35, 372), "[CRITICAL PLATFORM STARVATION CONFLICT DETECTED]", fill=(248, 113, 113, 255), font=font_bold)
        draw.text((35, 396), "Conflict: Train 12951 and Train 12004 scheduled on Platform 3 within 4 mins (< 15m minimum buffer).", fill=(254, 226, 226, 255), font=font_med)
        draw.text((35, 422), "GatiSetu AI Precedence Action: Reassigning Train 12004 to empty Platform 5 immediately...", fill=(252, 165, 165, 255), font=font_small)
    else:
        draw.rounded_rectangle([20, 360, 830, 460], radius=8, fill=(16, 185, 129, 35), outline=(16, 185, 129, 255), width=2)
        draw.text((35, 372), "[PLATFORM REALLOCATION RESOLVED BY GATISETU AI]", fill=(52, 211, 153, 255), font=font_bold)
        draw.text((35, 396), "Resolution: Train 12004 Shatabdi Express successfully assigned to Platform 5. Headway clear.", fill=(241, 245, 249, 255), font=font_med)
        draw.text((35, 422), "All passenger PIDS concourse screens and automated announcements updated across New Delhi Station.", fill=(110, 231, 183, 255), font=font_small)

    return img

def render_phase_3(frame_idx, total_p3_frames=30):
    """Passenger Android App Dynamic Route Progression & Offline BTS."""
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw_window_frame(draw, active_tab=2)
    
    prog = frame_idx / float(total_p3_frames - 1)
    
    # Sub-header with Indian Railways Mobile Delivery Styling
    draw.rounded_rectangle([20, 44, 185, 68], radius=6, fill=(30, 58, 138, 255), outline=(59, 130, 246, 255), width=1)
    draw.text((28, 48), "WHERE IS MY TRAIN", fill=(241, 245, 249, 255), font=font_bold)
    draw.text((215, 48), "OFFLINE PASSENGER TRACKING & BTS", fill=(241, 245, 249, 255), font=font_banner)
    draw.text((610, 50), "Zero-Internet Sensor Fusion", fill=(52, 211, 153, 255), font=font_small)
    
    # Left: Smartphone Live Timeline Representation
    draw.rounded_rectangle([20, 75, 440, 455], radius=10, fill=(15, 23, 42, 255), outline=(37, 99, 235, 255), width=2)
    draw.text((35, 87), "12951 MUMBAI TEJAS RAJDHANI", fill=(255, 255, 255, 255), font=font_bold)
    draw.text((35, 107), "Real-Time Station Progression & Scheduled vs Dynamic ETA", fill=(148, 163, 184, 255), font=font_small)
    
    # Vertical Route Line
    line_x = 75
    draw.line([(line_x, 140), (line_x, 420)], fill=(71, 85, 105, 255), width=4)
    
    stops = [
        (150, "NEW DELHI [NDLS]", "16:55", "16:55", "Departed On Time", (34, 197, 94, 255)),
        (220, "KOTA JN [KOTA]", "21:30", "21:42", "+12m (Physics Delay)", (239, 68, 68, 255)),
        (290, "RATLAM JN [RTM]", "01:10", "01:17", "+7m (WTT Slack Recovery)", (245, 158, 11, 255)),
        (360, "VADODARA [BRC]", "04:35", "04:38", "+3m (Recovering)", (34, 197, 94, 255)),
        (420, "MUMBAI CENTRAL [BCT]", "08:35", "08:35", "ON TIME Terminus", (34, 197, 94, 255))
    ]
    
    # Moving Train Marker on Route
    curr_marker_y = int(150 + prog * 200)
    
    for sy, sname, sta, eta, note, col in stops:
        is_passed = (sy < curr_marker_y)
        dot_col = (16, 185, 129, 255) if is_passed else (148, 163, 184, 255)
        draw.circle((line_x, sy), 6, fill=dot_col, outline=(15, 23, 42, 255), width=2)
        draw.text((line_x + 18, sy - 14), sname, fill=(241, 245, 249, 255), font=font_small)
        draw.text((line_x + 18, sy + 1), f"STA: {sta}  |  Dynamic ETA: {eta}", fill=(56, 189, 248, 255), font=font_small)
        draw.text((310, sy - 8), note, fill=col, font=font_small)
        
    # Train Locomotive Marker
    draw.circle((line_x, curr_marker_y), 11, fill=(239, 68, 68, 255), outline=(255, 255, 255, 255), width=2)
    draw.text((line_x - 30, curr_marker_y - 6), "🚆", fill=(255, 255, 255, 255))
    
    # Right: Dual-Mode Edge Sensor Fusion Box
    draw.rounded_rectangle([455, 75, 830, 255], radius=10, fill=(15, 23, 42, 255), outline=(30, 41, 59, 255), width=2)
    draw.text((470, 87), "DUAL-MODE EDGE SENSOR FUSION (OFFLINE BTS)", fill=(52, 211, 153, 255), font=font_bold)
    draw.text((470, 107), "Continuous tracking in tunnels and rural zero-internet dead zones", fill=(148, 163, 184, 255), font=font_small)
    
    fusion_items = [
        ("Base Station Triangulation", "MCC: 404 | MNC: 45 | LAC: 1204 | CID: 58291"),
        ("Local Railway Tower DB", "snapped to KP 412.8 km (Cross-Track Error: 12m)"),
        ("3-Axis Accelerometer IMU", f"Joint Vibration: {2.1 + math.sin(prog * 6) * 0.4:.2f} m/s^2 (Train Verified)"),
        ("Anti-Spoofing Filter", "Road Highway Vehicle Rejected (p < 0.001)"),
        ("Dead-Zone FIFO Buffer", "14 Telemetry Packets Queued for Reconnection")
    ]
    f_y = 125
    for fk, fv in fusion_items:
        draw.text((470, f_y), fk + ":", fill=(148, 163, 184, 255), font=font_small)
        draw.text((470, f_y + 14), fv, fill=(241, 245, 249, 255), font=font_small)
        f_y += 26
        
    # Right Bottom: Live Speedometer & Quantile Bounds
    draw.rounded_rectangle([455, 270, 830, 455], radius=10, fill=(15, 23, 42, 255), outline=(30, 41, 59, 255), width=2)
    draw.text((470, 282), "INSTANTANEOUS SPEED & PROBABILISTIC QUANTILE BOUNDS", fill=(245, 158, 11, 255), font=font_bold)
    
    speed = int(124 + math.sin(prog * 3.14) * 6)
    draw.text((470, 310), f"{speed}", fill=(56, 189, 248, 255), font=font_banner)
    draw.text((505, 314), "km/h", fill=(148, 163, 184, 255), font=font_med)
    draw.text((550, 314), "MPS Limit: 130 km/h | Throttle: 92% | Brake Pipe: 5.0 kg/cm^2", fill=(203, 213, 225, 255), font=font_small)
    
    # Quantile bounds visualization
    draw.text((470, 345), "Next Station: KOTA JN [KOTA] Probabilistic Arrival Window:", fill=(148, 163, 184, 255), font=font_small)
    draw.rounded_rectangle([470, 368, 570, 412], radius=6, fill=(30, 41, 59, 255))
    draw.text((482, 375), "P10 (Fast)", fill=(148, 163, 184, 255), font=font_small)
    draw.text((482, 391), "21:38", fill=(52, 211, 153, 255), font=font_bold)
    
    draw.rounded_rectangle([585, 368, 695, 412], radius=6, fill=(37, 99, 235, 40), outline=(59, 130, 246, 255), width=1)
    draw.text((597, 375), "P50 (Expected)", fill=(191, 219, 254, 255), font=font_small)
    draw.text((597, 391), "21:42", fill=(255, 255, 255, 255), font=font_bold)
    
    draw.rounded_rectangle([710, 368, 815, 412], radius=6, fill=(30, 41, 59, 255))
    draw.text((722, 375), "P90 (Worst)", fill=(148, 163, 184, 255), font=font_small)
    draw.text((722, 391), "21:49", fill=(248, 113, 113, 255), font=font_bold)
    
    draw.text((470, 428), "Guaranteed Monotonicity: P10 <= P50 <= P90 (Empirical MAE: 6.2 min)", fill=(110, 231, 183, 255), font=font_small)

    return img

print('Rendering frames...')
frames = []

# 28 frames for Phase 1
for i in range(28):
    frames.append(render_phase_1(i, 28))

# 28 frames for Phase 2
for i in range(28):
    frames.append(render_phase_2(i, 28))

# 28 frames for Phase 3
for i in range(28):
    frames.append(render_phase_3(i, 28))

print(f'Total frames rendered: {len(frames)}')

# Apply rounded corners to all frames
master_mask = Image.new('L', (W, H), 0)
mask_draw = ImageDraw.Draw(master_mask)
mask_draw.rounded_rectangle([0, 0, W - 1, H - 1], radius=RADIUS, fill=255)

rounded_frames = []
for f in frames:
    frame_copy = f.copy()
    frame_copy.putalpha(master_mask)
    rounded_frames.append(frame_copy)

out_gif_path = '/Users/toru/Projects/rail-reverse-engine/assets/demo.gif'

# Quantize and save as GIF
print('Quantizing and saving demo.gif...')
palette_img = rounded_frames[0].convert('P', palette=Image.Palette.ADAPTIVE, colors=256)

quantized_frames = []
for f in rounded_frames:
    q = f.convert('RGB').quantize(colors=256, palette=palette_img)
    quantized_frames.append(q)

quantized_frames[0].save(
    out_gif_path,
    save_all=True,
    append_images=quantized_frames[1:],
    duration=100, # 100ms per frame
    loop=0,       # infinite loop
    optimize=True
)

file_size_mb = os.path.getsize(out_gif_path) / (1024.0 * 1024.0)
print(f'Saved demo.gif: {out_gif_path} ({file_size_mb:.2f} MB, {len(quantized_frames)} frames)')
