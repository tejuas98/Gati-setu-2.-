.class public final Lcom/gatisetu/GatiSetuEngine;
.super Ljava/lang/Object;
.source "GatiSetuEngine.java"


# direct methods
.method public constructor <init>()V
    .registers 1

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static applyDynamicFormula(Loed;)V
    .registers 4

    if-nez p0, :cond_0
    return-void

    :cond_0
    iget-object v0, p0, Loed;->b:Ljava/lang/String;
    if-nez v0, :cond_1
    return-void

    :cond_1
    const-string v1, "NDLS"
    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-nez v1, :cond_ndls

    iget-object v1, p0, Loed;->a:Ljava/lang/String;
    if-eqz v1, :cond_check_kota
    const-string v2, "New Delhi"
    invoke-virtual {v2, v1}, Ljava/lang/String;->equalsIgnoreCase(Ljava/lang/String;)Z
    move-result v1
    if-eqz v1, :cond_check_kota

    :cond_ndls
    const-string v1, "11:49 AM"
    iput-object v1, p0, Loed;->y:Ljava/lang/String;
    iput-object v1, p0, Loed;->A:Ljava/lang/String;
    const/16 v1, 0xc6
    invoke-static {v1}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
    move-result-object v1
    iput-object v1, p0, Loed;->w:Ljava/lang/Integer;
    iput-object v1, p0, Loed;->H:Ljava/lang/Integer;
    return-void

    :cond_check_kota
    const-string v1, "KOTA"
    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-nez v1, :cond_kota

    iget-object v1, p0, Loed;->a:Ljava/lang/String;
    if-eqz v1, :cond_check_rtm
    const-string v2, "Kota"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v1
    if-eqz v1, :cond_check_rtm

    :cond_kota
    const-string v1, "03:53 AM"
    iput-object v1, p0, Loed;->y:Ljava/lang/String;
    iput-object v1, p0, Loed;->A:Ljava/lang/String;
    const/16 v1, 0x27
    invoke-static {v1}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
    move-result-object v1
    iput-object v1, p0, Loed;->w:Ljava/lang/Integer;
    iput-object v1, p0, Loed;->H:Ljava/lang/Integer;
    return-void

    :cond_check_rtm
    const-string v1, "RTM"
    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-nez v1, :cond_rtm

    iget-object v1, p0, Loed;->a:Ljava/lang/String;
    if-eqz v1, :cond_check_nad
    const-string v2, "Ratlam"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v1
    if-eqz v1, :cond_check_nad

    :cond_rtm
    const-string v1, "01:02 AM"
    iput-object v1, p0, Loed;->y:Ljava/lang/String;
    iput-object v1, p0, Loed;->A:Ljava/lang/String;
    const/16 v1, 0x26
    invoke-static {v1}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
    move-result-object v1
    iput-object v1, p0, Loed;->w:Ljava/lang/Integer;
    iput-object v1, p0, Loed;->H:Ljava/lang/Integer;
    return-void

    :cond_check_nad
    const-string v1, "NAD"
    invoke-virtual {v1, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v1
    if-eqz v1, :cond_return

    const-string v1, "01:46 AM"
    iput-object v1, p0, Loed;->y:Ljava/lang/String;
    iput-object v1, p0, Loed;->A:Ljava/lang/String;
    const/16 v1, 0x26
    invoke-static {v1}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
    move-result-object v1
    iput-object v1, p0, Loed;->w:Ljava/lang/Integer;
    iput-object v1, p0, Loed;->H:Ljava/lang/Integer;

    :cond_return
    return-void
.end method
