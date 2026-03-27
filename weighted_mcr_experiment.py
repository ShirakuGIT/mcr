import heapq, random, math
import numpy as np
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DARK="#0d1117";PANEL="#161b22";BORDER="#30363d";GREEN="#2ea55a";YELLOW="#f0c040"
RED="#f85149";BLUE="#60a5fa";GREY="#8b949e";ORANGE="#fb923c";PURPLE="#c084fc";TEAL="#2dd4bf"
plt.rcParams.update({"figure.facecolor":DARK,"axes.facecolor":PANEL,"axes.edgecolor":BORDER,
    "text.color":"#e6edf3","axes.labelcolor":"#e6edf3","xtick.color":GREY,"ytick.color":GREY,
    "grid.color":BORDER,"grid.linewidth":0.5,"font.family":"monospace","axes.titlesize":10})

def weighted_greedy_mcr(G,C,w,s,t):
    def wcost(S): return sum(w.get(i,0.0) for i in S)
    dist={v:float('inf') for v in G.nodes()}; best_S={v:frozenset() for v in G.nodes()}; prev={v:None for v in G.nodes()}
    dist[s]=wcost(C.get(s,frozenset())); best_S[s]=C.get(s,frozenset()); pq=[(dist[s],s)]
    while pq:
        cu,u=heapq.heappop(pq)
        if cu>dist[u]: continue
        if u==t: break
        for v in G.neighbors(u):
            nS=best_S[u]|C.get(v,frozenset()); nc=wcost(nS)
            if nc<dist[v]: dist[v]=nc; best_S[v]=nS; prev[v]=u; heapq.heappush(pq,(nc,v))
    if dist[t]==float('inf'): return None,None,None
    path=[]; cur=t
    while cur is not None: path.append(cur); cur=prev[cur]
    return dist[t],best_S[t],list(reversed(path))

def standard_greedy_mcr(G,C,s,t):
    uw={c:1.0 for ncs in C.values() for c in ncs}
    return weighted_greedy_mcr(G,C,uw,s,t)

# Exp3
def run_trial(seed):
    rng=random.Random(seed)
    G=nx.erdos_renyi_graph(15,0.30,seed=seed)
    if not nx.is_connected(G):
        G=G.subgraph(max(nx.connected_components(G),key=len)).copy(); G=nx.convert_node_labels_to_integers(G)
    if len(G)<4: return None
    nodes=list(G.nodes()); s,t=nodes[0],nodes[-1]
    if s==t: return None
    M=8; cids=list(range(M))
    C={v:frozenset(rng.sample(cids,rng.randint(0,3))) for v in G.nodes()}
    C[s]=frozenset(); C[t]=frozenset()
    w={i:round(10**rng.uniform(-1,1.5),2) for i in cids}
    sc,sS,sp=standard_greedy_mcr(G,C,s,t); wc,wS,wp=weighted_greedy_mcr(G,C,w,s,t)
    if sc is None or wc is None: return None
    sw=sum(w.get(c,0) for c in sS) if sS else 0.0
    return {"std_k":int(sc),"wgt_k":len(wS),"std_wcost":sw,"wgt_wcost":wc,
            "differ":sp!=wp,"w_save":sw-wc,"k_delta":len(wS)-int(sc)}

# 2D scene: two barrier strips that robot must cross
# Barrier 1 (y=3.5-4.5): Table covers x=0-5.5 (heavy), Chair_A covers x=5.5-9.5 (light)
# Barrier 2 (y=6.0-6.8): Cabinet covers x=0-5.5 (medium), Chair_B covers x=5.5-9.5 (light)
# Three passage corridors through the barriers:
#   Left passage (x~1):  goes through Table (w=10) + Cabinet (w=8) -- VERY HEAVY
#   Mid passage (x~5.2): tiny gap but touches both barriers at Table+Cabinet edge -- heavy
#   Right passage(x~7):  goes through Chair_A (w=1) + Chair_B (w=1) -- LIGHT
# Standard MCR might pick fewest unique obstacle count, Weighted will go right to dodge heavy ones

OBS=[
    # Barrier 1
    ("Table",   0.0, 3.5, 5.2, 1.0, 10.0, RED),
    ("Chair_A", 5.2, 3.5, 4.3, 1.0,  1.0, BLUE),
    # Barrier 2
    ("Cabinet", 0.0, 6.0, 5.2, 0.8,  8.0, ORANGE),
    ("Chair_B", 5.2, 6.0, 4.3, 0.8,  1.0, BLUE),
    # Extra obstacle cluster forcing detour
    ("Shelf",   3.5, 1.5, 1.5, 0.7,  3.0, PURPLE),
]
WW,WH=9.5,9.5; START=(0.5,0.5); GOAL=(9.0,9.0)
weights_scene={nm:wv for nm,_,_,_,_,wv,_ in OBS}

def in_rect(px,py,ox,oy,ow,oh,m=0.06):
    return ox-m<=px<=ox+ow+m and oy-m<=py<=oy+oh+m

def seg_hits_rect(p1,p2,ox,oy,ow,oh):
    x1,y1=p1; x2,y2=p2; dx,dy=x2-x1,y2-y1; tmin,tmax=0.0,1.0
    for pn,qn in [(-dx,x1-ox),(dx,ox+ow-x1),(-dy,y1-oy),(dy,oy+oh-y1)]:
        if pn==0:
            if qn<0: return False
        else:
            t=qn/pn
            if pn<0: tmin=max(tmin,t)
            else: tmax=min(tmax,t)
        if tmin>tmax: return False
    return True

def node_cov(px,py):
    return frozenset(nm for nm,ox,oy,ow,oh,_,_ in OBS if in_rect(px,py,ox,oy,ow,oh))

def edge_cov(p1,p2):
    cs=set()
    for t in np.linspace(0,1,16):
        cs|=node_cov(p1[0]+t*(p2[0]-p1[0]),p1[1]+t*(p2[1]-p1[1]))
    for nm,ox,oy,ow,oh,_,_ in OBS:
        if seg_hits_rect(p1,p2,ox,oy,ow,oh): cs.add(nm)
    return frozenset(cs)

def build_prm(n_mil=220, cr=2.0, seed=77):
    rng=random.Random(seed)
    pts=[START,GOAL]
    while len(pts)<n_mil+2:
        pts.append((rng.uniform(0.2,WW-0.2),rng.uniform(0.2,WH-0.2)))
    nr=len(pts); G=nx.Graph(); pos={}; C={}
    for i,(px,py) in enumerate(pts): G.add_node(i); pos[i]=(px,py); C[i]=node_cov(px,py)
    nid=nr
    for i in range(nr):
        for j in range(i+1,nr):
            px1,py1=pos[i]; px2,py2=pos[j]
            if math.hypot(px1-px2,py1-py2)<=cr:
                ec=C[i]|C[j]|edge_cov(pos[i],pos[j])
                extra=ec-C[i]-C[j]
                if extra:
                    mx,my=(px1+px2)/2,(py1+py2)/2
                    G.add_node(nid); pos[nid]=(mx,my); C[nid]=ec
                    G.add_edge(i,nid); G.add_edge(nid,j); nid+=1
                else:
                    G.add_edge(i,j)
    return G,C,pos,0,1,nr

def draw_scene(ax,G,C,pos,nr,s,t,paths_labels,obs,title,info=""):
    ax.set_facecolor(PANEL); ax.set_xlim(-0.3,WW+0.3); ax.set_ylim(-0.3,WH+0.3); ax.set_aspect("equal")
    for nm,ox,oy,ow,oh,wv,col in obs:
        ax.add_patch(plt.Rectangle((ox,oy),ow,oh,fc=col+"28",ec=col,lw=2,zorder=2))
        ax.text(ox+ow/2,oy+oh/2,f"{nm}\nw={wv:.0f}",ha="center",va="center",
                fontsize=6.5,color=col,fontweight="bold",zorder=5)
    real=set(range(nr))
    for u,v in G.edges():
        if u in real and v in real:
            p1,p2=pos[u],pos[v]
            ax.plot([p1[0],p2[0]],[p1[1],p2[1]],color=BORDER,lw=0.28,alpha=0.32,zorder=1)
    for v in real:
        p=pos[v]; nc=len(C.get(v,frozenset()))
        c=[GREY,YELLOW,ORANGE,RED][min(nc,3)]
        ax.scatter(*p,s=6 if nc==0 else 14,c=c,zorder=6,alpha=0.5,linewidths=0)
    lstyles=[("-",3.5),("--",2.5)]
    for idx,(path,label,col) in enumerate(paths_labels):
        if not path: continue
        coords=[pos[v] for v in path if v in pos]
        xs=[c[0] for c in coords]; ys=[c[1] for c in coords]
        ls,lw=lstyles[idx] if idx<2 else ("-",2)
        ax.plot(xs,ys,color=col,lw=lw,ls=ls,zorder=12,label=label,solid_capstyle="round")
        if len(xs)>=2:
            ax.annotate("",xy=(xs[-1],ys[-1]),xytext=(xs[-2],ys[-2]),
                        arrowprops=dict(arrowstyle="-|>",color=col,lw=lw),zorder=13)
    ax.scatter(*pos[s],s=280,c=GREEN,marker="*",zorder=15)
    ax.scatter(*pos[t],s=280,c=RED,  marker="*",zorder=15)
    ax.text(pos[s][0]+0.22,pos[s][1]+0.1,"S",fontsize=11,color=GREEN,fontweight="bold",zorder=16)
    ax.text(pos[t][0]+0.22,pos[t][1]+0.1,"G",fontsize=11,color=RED,  fontweight="bold",zorder=16)
    ax.set_title(title,pad=8); ax.set_xlabel("x (m)"); ax.set_ylabel("y (m)")
    if info:
        ax.text(0.01,0.01,info,transform=ax.transAxes,fontsize=7.5,va="bottom",
                color="#e6edf3",bbox=dict(fc=DARK,ec=BORDER,pad=3,alpha=0.9),zorder=20)
    ax.legend(loc="upper left",fontsize=7,facecolor=DARK,edgecolor=BORDER,labelcolor="#e6edf3")

print("Building PRM...")
G,C,pos,s_nd,t_nd,n_real=build_prm()
print(f"  PRM: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges, path exists: {nx.has_path(G,s_nd,t_nd)}")

std_c,std_S,std_p=standard_greedy_mcr(G,C,s_nd,t_nd)
wgt_c,wgt_S,wgt_p=weighted_greedy_mcr(G,C,weights_scene,s_nd,t_nd)
std_wc=sum(weights_scene.get(c,0) for c in std_S) if std_S else 0
print(f"  Standard MCR: |S|={std_c}  S={sorted(std_S)}  w-cost={std_wc:.1f}")
print(f"  Weighted MCR: |S|={len(wgt_S)}  S={sorted(wgt_S)}  w-cost={wgt_c:.1f}")
print(f"  Saving={std_wc-wgt_c:.1f}  k_delta={len(wgt_S)-int(std_c):+d}")

print("Running Exp 3 (500 trials)...")
r3=[r for r in (run_trial(s) for s in range(500)) if r is not None]
differ=[r for r in r3 if r["differ"]]; k_more=[r for r in differ if r["k_delta"]>0]
w_saves_pos=[r["w_save"] for r in r3 if r["w_save"]>0.01]
n_same_path=len(r3)-len(differ)
n_diff_same_k_cheap=sum(1 for r in differ if r["k_delta"]==0 and r["w_save"]>0.01)
n_more_cheap=len(k_more)
n_no_save=len(differ)-n_diff_same_k_cheap-n_more_cheap

print(f"  Valid trials: {len(r3)}, paths differ: {len(differ)} ({100*len(differ)/len(r3):.1f}%)")
print(f"  Key tradeoff (more |S|, cheaper w): {len(k_more)} ({100*len(k_more)/len(r3):.1f}%)")
print(f"  Weighted cheaper: {len(w_saves_pos)} ({100*len(w_saves_pos)/len(r3):.1f}%)")
print(f"\n  EXP 3 BUG WAS: 'standard_saves = std_cost - wgt_k'")
print(f"  This asks: does standard use MORE obstacles than weighted?")
print(f"  Answer is almost never YES because standard MINIMISES |S|.")
print(f"  Correct metrics: w_save and k_delta, measured separately.")

fig=plt.figure(figsize=(18,13),facecolor=DARK)
fig.suptitle("Semantically Weighted MCR  vs  Standard MCR  |  2D C-Space + Fixed Experiment 3",
             fontsize=12,fontweight="bold",color="#e6edf3",y=0.99)
gs=fig.add_gridspec(2,3,hspace=0.45,wspace=0.34,left=0.05,right=0.97,top=0.95,bottom=0.06)
ax1=fig.add_subplot(gs[0,0]); ax2=fig.add_subplot(gs[0,1]); ax3=fig.add_subplot(gs[0,2])
ax4=fig.add_subplot(gs[1,0]); ax5=fig.add_subplot(gs[1,1]); ax6=fig.add_subplot(gs[1,2])

draw_scene(ax1,G,C,pos,n_real,s_nd,t_nd,
    [(std_p,f"Standard: |S|={std_c} w-cost={std_wc:.0f}",RED)],OBS,
    "Standard Greedy MCR (minimise |S|)",
    f"S = {{{', '.join(sorted(std_S))}}}\n|S| = {std_c}  semantic cost = {std_wc:.0f}")

draw_scene(ax2,G,C,pos,n_real,s_nd,t_nd,
    [(wgt_p,f"Weighted: |S|={len(wgt_S)} w-cost={wgt_c:.0f}",GREEN)],OBS,
    "Weighted Greedy MCR (minimise Σwᵢ)",
    f"S = {{{', '.join(sorted(wgt_S))}}}\n|S| = {len(wgt_S)}  semantic cost = {wgt_c:.0f}")

draw_scene(ax3,G,C,pos,n_real,s_nd,t_nd,
    [(std_p,f"Standard |S|={std_c} w={std_wc:.0f}",RED),
     (wgt_p,f"Weighted |S|={len(wgt_S)} w={wgt_c:.0f}",GREEN)],OBS,
    "Overlay",
    f"k_delta = {len(wgt_S)-int(std_c):+d} obstacles\n"
    f"semantic saving = {std_wc-wgt_c:.0f}\n"
    f"Weighted avoids heavy obstacles\n(Table w=10, Cabinet w=8)")

k_deltas=[r["k_delta"] for r in r3]; w_saves_all=[r["w_save"] for r in r3]
pt_cols=[GREEN if r["w_save"]>0.01 else (RED if r["w_save"]<-0.01 else GREY) for r in r3]
ax4.scatter(k_deltas,w_saves_all,s=12,c=pt_cols,alpha=0.45,zorder=3)
ax4.axhline(0,color=GREY,lw=0.8,ls="--"); ax4.axvline(0,color=GREY,lw=0.8,ls="--")
for tx,ty,lbl,c in [(0.82,0.88,"MORE |S|\ncheaper w\n← KEY",GREEN),
                     (0.14,0.88,"fewer |S|\ncheaper w",BLUE),
                     (0.82,0.12,"more |S|\ncostlier",RED),
                     (0.14,0.12,"tied",GREY)]:
    ax4.text(tx,ty,lbl,transform=ax4.transAxes,fontsize=6.8,color=c,ha="center",va="center",
             bbox=dict(fc=DARK,ec=c,pad=2,alpha=0.85))
ax4.set_xlabel("|S_weighted| − |S_standard|  (k_delta)"); ax4.set_ylabel("semantic cost saving")
ax4.set_title(f"Exp 3 (FIXED) — Core Tradeoff  (n={len(r3)})\n"
              f"Top-right (KEY): {len(k_more)} trials ({100*len(k_more)/len(r3):.1f}%) — weighted trades |S| for lower w-cost",pad=8)
ax4.grid(True,alpha=0.3)

ax5.hist(w_saves_all,bins=40,color=BLUE,edgecolor=DARK,alpha=0.85)
ax5.axvline(0,color=GREY,lw=1.2,ls="--",label="break-even")
if w_saves_pos: ax5.axvline(np.mean(w_saves_pos),color=YELLOW,lw=2,label=f"mean saving={np.mean(w_saves_pos):.1f}")
ax5.set_xlabel("semantic saving  (std_w_cost − wgt_w_cost)"); ax5.set_ylabel("count")
ax5.set_title(f"Exp 3 — Semantic Savings\n{len(w_saves_pos)}/{len(r3)} ({100*len(w_saves_pos)/len(r3):.1f}%) trials: weighted is cheaper",pad=8)
ax5.legend(fontsize=7.5,facecolor=PANEL,edgecolor=BORDER,labelcolor="#e6edf3"); ax5.grid(True,axis="y",alpha=0.4)

cats=["paths\nidentical","diff path\nsame |S|\ncheaper w","diff path\nMORE |S|\ncheaper w\n(KEY)","diff path\nno saving"]
vals=[n_same_path,n_diff_same_k_cheap,n_more_cheap,n_no_save]; bcols=[GREY,BLUE,GREEN,RED]
bars=ax6.bar(cats,vals,color=bcols,edgecolor=DARK,width=0.55)
for bar,val in zip(bars,vals):
    ax6.text(bar.get_x()+bar.get_width()/2,bar.get_height()+2,
             f"{val}\n({100*val/len(r3):.0f}%)",ha="center",fontsize=8.5,color="#e6edf3")
ax6.set_ylabel("count"); ax6.set_ylim(0,max(vals)*1.32)
ax6.set_title(f"Exp 3 — Outcome Breakdown ({len(r3)} trials)",pad=8)
ax6.grid(True,axis="y",alpha=0.4)

out="weighted_mcr_v2.png"
plt.savefig(out,dpi=150,bbox_inches="tight",facecolor=DARK)
print(f"Saved -> {out}")
