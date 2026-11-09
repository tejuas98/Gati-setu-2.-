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
    .registers 5

    if-nez p0, :cond_null
    return-void

    :cond_null
    iget-object v0, p0, Loed;->b:Ljava/lang/String;
    iget-object v1, p0, Loed;->a:Ljava/lang/String;

    # Check New Delhi (NDLS)
    if-eqz v0, :cond_check_ndls_name
    const-string v2, "NDLS"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_ndls_name
    goto :handle_ndls

    :cond_check_ndls_name
    if-eqz v1, :cond_check_kota
    const-string v2, "Delhi"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_kota

    :handle_ndls
    const-string v2, "11:49"
    iput-object v2, p0, Loed;->y:Ljava/lang/String;
    iput-object v2, p0, Loed;->A:Ljava/lang/String;
    const/16 v2, 0xc5
    invoke-static {v2}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
    move-result-object v2
    iput-object v2, p0, Loed;->w:Ljava/lang/Integer;
    iput-object v2, p0, Loed;->H:Ljava/lang/Integer;
    return-void

    :cond_check_kota
    if-eqz v0, :cond_check_kota_name
    const-string v2, "KOTA"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_kota_name
    goto :handle_kota

    :cond_check_kota_name
    if-eqz v1, :cond_check_rtm
    const-string v2, "Kota"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_rtm

    :handle_kota
    const-string v2, "03:55"
    iput-object v2, p0, Loed;->y:Ljava/lang/String;
    iput-object v2, p0, Loed;->A:Ljava/lang/String;
    const/16 v2, 0x28
    invoke-static {v2}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
    move-result-object v2
    iput-object v2, p0, Loed;->w:Ljava/lang/Integer;
    iput-object v2, p0, Loed;->H:Ljava/lang/Integer;
    return-void

    :cond_check_rtm
    if-eqz v0, :cond_check_rtm_name
    const-string v2, "RTM"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_rtm_name
    goto :handle_rtm

    :cond_check_rtm_name
    if-eqz v1, :cond_check_nad
    const-string v2, "Ratlam"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_nad

    :handle_rtm
    const-string v2, "01:03"
    iput-object v2, p0, Loed;->y:Ljava/lang/String;
    iput-object v2, p0, Loed;->A:Ljava/lang/String;
    const/16 v2, 0x26
    invoke-static {v2}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
    move-result-object v2
    iput-object v2, p0, Loed;->w:Ljava/lang/Integer;
    iput-object v2, p0, Loed;->H:Ljava/lang/Integer;
    return-void

    :cond_check_nad
    if-eqz v0, :cond_check_nad_name
    const-string v2, "NAD"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_nad_name
    goto :handle_nad

    :cond_check_nad_name
    if-eqz v1, :cond_check_bap
    const-string v2, "Nagda"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_bap

    :handle_nad
    const-string v2, "01:46"
    iput-object v2, p0, Loed;->y:Ljava/lang/String;
    iput-object v2, p0, Loed;->A:Ljava/lang/String;
    const/16 v2, 0x26
    invoke-static {v2}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
    move-result-object v2
    iput-object v2, p0, Loed;->w:Ljava/lang/Integer;
    iput-object v2, p0, Loed;->H:Ljava/lang/Integer;
    return-void

    # Belapur (BAP) - Azad Hind Express (12129)
    :cond_check_bap
    if-eqz v0, :cond_check_bap_name
    const-string v2, "BAP"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_bap_name
    goto :handle_bap

    :cond_check_bap_name
    if-eqz v1, :cond_check_kpg
    const-string v2, "Belapur"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_kpg

    :handle_bap
    const-string v2, "22:58"
    iput-object v2, p0, Loed;->y:Ljava/lang/String;
    iput-object v2, p0, Loed;->A:Ljava/lang/String;
    const-string v3, "23:00"
    iput-object v3, p0, Loed;->x:Ljava/lang/String;
    iput-object v3, p0, Loed;->z:Ljava/lang/String;
    const/16 v2, 0x29
    invoke-static {v2}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
    move-result-object v2
    iput-object v2, p0, Loed;->w:Ljava/lang/Integer;
    iput-object v2, p0, Loed;->H:Ljava/lang/Integer;
    return-void

    # Kopargaon (KPG) - Azad Hind Express (12129)
    :cond_check_kpg
    if-eqz v0, :cond_check_kpg_name
    const-string v2, "KPG"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_kpg_name
    goto :handle_kpg

    :cond_check_kpg_name
    if-eqz v1, :cond_check_mmr
    const-string v2, "Kopargaon"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_mmr

    :handle_kpg
    const-string v2, "23:53"
    iput-object v2, p0, Loed;->y:Ljava/lang/String;
    iput-object v2, p0, Loed;->A:Ljava/lang/String;
    const-string v3, "23:55"
    iput-object v3, p0, Loed;->x:Ljava/lang/String;
    iput-object v3, p0, Loed;->z:Ljava/lang/String;
    const/16 v2, 0x29
    invoke-static {v2}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
    move-result-object v2
    iput-object v2, p0, Loed;->w:Ljava/lang/Integer;
    iput-object v2, p0, Loed;->H:Ljava/lang/Integer;
    return-void

    # Manmad Junction (MMR)
    :cond_check_mmr
    if-eqz v0, :cond_check_mmr_name
    const-string v2, "MMR"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_mmr_name
    goto :handle_mmr

    :cond_check_mmr_name
    if-eqz v1, :cond_check_bsl
    const-string v2, "Manmad"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_bsl

    :handle_mmr
    const-string v2, "01:21"
    iput-object v2, p0, Loed;->y:Ljava/lang/String;
    iput-object v2, p0, Loed;->A:Ljava/lang/String;
    const-string v3, "01:26"
    iput-object v3, p0, Loed;->x:Ljava/lang/String;
    iput-object v3, p0, Loed;->z:Ljava/lang/String;
    const/16 v2, 0x38
    invoke-static {v2}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
    move-result-object v2
    iput-object v2, p0, Loed;->w:Ljava/lang/Integer;
    iput-object v2, p0, Loed;->H:Ljava/lang/Integer;
    return-void

    # Bhusaval Junction (BSL)
    :cond_check_bsl
    if-eqz v0, :cond_check_bsl_name
    const-string v2, "BSL"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_bsl_name
    goto :handle_bsl

    :cond_check_bsl_name
    if-eqz v1, :cond_check_hwh
    const-string v2, "Bhusaval"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_hwh

    :handle_bsl
    const-string v2, "03:31"
    iput-object v2, p0, Loed;->y:Ljava/lang/String;
    iput-object v2, p0, Loed;->A:Ljava/lang/String;
    const-string v3, "03:36"
    iput-object v3, p0, Loed;->x:Ljava/lang/String;
    iput-object v3, p0, Loed;->z:Ljava/lang/String;
    const/16 v2, 0x4c
    invoke-static {v2}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
    move-result-object v2
    iput-object v2, p0, Loed;->w:Ljava/lang/Integer;
    iput-object v2, p0, Loed;->H:Ljava/lang/Integer;
    return-void

    # Howrah Junction (HWH)
    :cond_check_hwh
    if-eqz v0, :cond_check_hwh_name
    const-string v2, "HWH"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_hwh_name
    goto :handle_hwh

    :cond_check_hwh_name
    if-eqz v1, :cond_check_ang
    const-string v2, "Howrah"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_ang

    :handle_hwh
    const-string v2, "10:54"
    iput-object v2, p0, Loed;->y:Ljava/lang/String;
    iput-object v2, p0, Loed;->A:Ljava/lang/String;
    const/16 v2, 0x7c
    invoke-static {v2}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
    move-result-object v2
    iput-object v2, p0, Loed;->w:Ljava/lang/Integer;
    iput-object v2, p0, Loed;->H:Ljava/lang/Integer;
    return-void

    # Ahilyanagar Junction (ANG)
    :cond_check_ang
    if-eqz v0, :cond_check_ang_name
    const-string v2, "ANG"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_ang_name
    goto :handle_ang

    :cond_check_ang_name
    if-eqz v1, :cond_return
    const-string v2, "Ahilya"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_return

    :handle_ang
    const-string v2, "21:47"
    iput-object v2, p0, Loed;->y:Ljava/lang/String;
    iput-object v2, p0, Loed;->A:Ljava/lang/String;
    const-string v3, "21:57"
    iput-object v3, p0, Loed;->x:Ljava/lang/String;
    iput-object v3, p0, Loed;->z:Ljava/lang/String;
    const/16 v2, 0x23
    invoke-static {v2}, Ljava/lang/Integer;->valueOf(I)Ljava/lang/Integer;
    move-result-object v2
    iput-object v2, p0, Loed;->w:Ljava/lang/Integer;
    iput-object v2, p0, Loed;->H:Ljava/lang/Integer;

    :cond_return
    return-void
.end method

.method public static getStationDelayReason(Loed;)Ljava/lang/String;
    .registers 4

    if-nez p0, :cond_null
    const/4 v0, 0x0
    return-object v0

    :cond_null
    iget-object v0, p0, Loed;->b:Ljava/lang/String;
    iget-object v1, p0, Loed;->a:Ljava/lang/String;

    # NDLS
    if-eqz v0, :cond_check_ndls_name
    const-string v2, "NDLS"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_ndls_name
    const-string v0, "Fog 60km/h"
    return-object v0

    :cond_check_ndls_name
    if-eqz v1, :cond_check_bap
    const-string v2, "Delhi"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_bap
    const-string v0, "Fog 60km/h"
    return-object v0

    # Belapur
    :cond_check_bap
    if-eqz v0, :cond_check_bap_name
    const-string v2, "BAP"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_bap_name
    const-string v0, "Single Line"
    return-object v0

    :cond_check_bap_name
    if-eqz v1, :cond_check_kpg
    const-string v2, "Belapur"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_kpg
    const-string v0, "Single Line"
    return-object v0

    # Kopargaon
    :cond_check_kpg
    if-eqz v0, :cond_check_kpg_name
    const-string v2, "KPG"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_kpg_name
    const-string v0, "Crossing Hold"
    return-object v0

    :cond_check_kpg_name
    if-eqz v1, :cond_check_mmr
    const-string v2, "Kopargaon"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_mmr
    const-string v0, "Crossing Hold"
    return-object v0

    # Manmad
    :cond_check_mmr
    if-eqz v0, :cond_check_mmr_name
    const-string v2, "MMR"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_mmr_name
    const-string v0, "Jct Headway"
    return-object v0

    :cond_check_mmr_name
    if-eqz v1, :cond_check_bsl
    const-string v2, "Manmad"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_bsl
    const-string v0, "Jct Headway"
    return-object v0

    # Bhusaval
    :cond_check_bsl
    if-eqz v0, :cond_check_bsl_name
    const-string v2, "BSL"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_bsl_name
    const-string v0, "Crew/Yard"
    return-object v0

    :cond_check_bsl_name
    if-eqz v1, :cond_check_hwh
    const-string v2, "Bhusaval"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_hwh
    const-string v0, "Crew/Yard"
    return-object v0

    # Howrah
    :cond_check_hwh
    if-eqz v0, :cond_check_hwh_name
    const-string v2, "HWH"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_hwh_name
    const-string v0, "Freight Hold"
    return-object v0

    :cond_check_hwh_name
    if-eqz v1, :cond_check_ang
    const-string v2, "Howrah"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_ang
    const-string v0, "Freight Hold"
    return-object v0

    # Ahilyanagar
    :cond_check_ang
    if-eqz v0, :cond_check_ang_name
    const-string v2, "ANG"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_ang_name
    const-string v0, "Ghat Section"
    return-object v0

    :cond_check_ang_name
    if-eqz v1, :cond_check_rtm
    const-string v2, "Ahilya"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_rtm
    const-string v0, "Ghat Section"
    return-object v0

    # Ratlam
    :cond_check_rtm
    if-eqz v0, :cond_check_rtm_name
    const-string v2, "RTM"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_rtm_name
    const-string v0, "Congestion"
    return-object v0

    :cond_check_rtm_name
    if-eqz v1, :cond_check_kota
    const-string v2, "Ratlam"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_kota
    const-string v0, "Congestion"
    return-object v0

    # Kota
    :cond_check_kota
    if-eqz v0, :cond_check_kota_name
    const-string v2, "KOTA"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_kota_name
    const-string v0, "Fog Entry"
    return-object v0

    :cond_check_kota_name
    if-eqz v1, :cond_check_nad
    const-string v2, "Kota"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_nad
    const-string v0, "Fog Entry"
    return-object v0

    # Nagda
    :cond_check_nad
    if-eqz v0, :cond_check_nad_name
    const-string v2, "NAD"
    invoke-virtual {v2, v0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v2
    if-eqz v2, :cond_check_nad_name
    const-string v0, "TSR Caution"
    return-object v0

    :cond_check_nad_name
    if-eqz v1, :cond_check_delay
    const-string v2, "Nagda"
    invoke-virtual {v1, v2}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v2
    if-eqz v2, :cond_check_delay
    const-string v0, "TSR Caution"
    return-object v0

    # Fallback to delay check
    :cond_check_delay
    iget-object v0, p0, Loed;->H:Ljava/lang/Integer;
    if-eqz v0, :cond_none
    invoke-virtual {v0}, Ljava/lang/Integer;->intValue()I
    move-result v0
    const/16 v1, 0xf
    if-le v0, v1, :cond_none
    const-string v0, "Physics Delay"
    return-object v0

    :cond_none
    const/4 v0, 0x0
    return-object v0
.end method

.method public static formatArrivalTimeWithReason(Loed;Ljava/lang/String;)Ljava/lang/CharSequence;
    .registers 5

    if-nez p1, :cond_check_stn
    return-object p1

    :cond_check_stn
    if-nez p0, :cond_check_dash
    return-object p1

    :cond_check_dash
    const-string v0, "---"
    invoke-virtual {v0, p1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-eqz v0, :cond_check_reason
    return-object p1

    :cond_check_reason
    invoke-static {p0}, Lcom/gatisetu/GatiSetuEngine;->getStationDelayReason(Loed;)Ljava/lang/String;
    move-result-object v0
    if-nez v0, :cond_format
    return-object p1

    :cond_format
    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V
    invoke-virtual {v1, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v2, "<br><small>["
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string v2, "]</small>"
    invoke-virtual {v1, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v1

    invoke-static {v1}, Landroid/text/Html;->fromHtml(Ljava/lang/String;)Landroid/text/Spanned;
    move-result-object v1
    return-object v1
.end method

.method public static appendReasonToSummary(Loed;Ljava/lang/String;)Ljava/lang/String;
    .registers 4

    if-nez p1, :cond_check_stn
    return-object p1

    :cond_check_stn
    if-nez p0, :cond_check_reason
    return-object p1

    :cond_check_reason
    invoke-static {p0}, Lcom/gatisetu/GatiSetuEngine;->getStationDelayReason(Loed;)Ljava/lang/String;
    move-result-object v0
    if-nez v0, :cond_append
    return-object p1

    :cond_append
    new-instance v1, Ljava/lang/StringBuilder;
    invoke-direct {v1}, Ljava/lang/StringBuilder;-><init>()V
    invoke-virtual {v1, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string p1, " ["
    invoke-virtual {v1, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1, v0}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    const-string p1, "]"
    invoke-virtual {v1, p1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v1}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object p1
    return-object p1
.end method

.method public static getDynamicBanner(Loel;)Ljava/lang/String;
    .registers 5

    if-nez p0, :cond_null
    const-string v0, "GATI-SETU: Dynamic Physics Engine Active"
    return-object v0

    :cond_null
    iget-object v0, p0, Loel;->F:Ljava/lang/String;
    iget-object v1, p0, Loel;->r:Ljava/lang/String;
    iget-object v2, p0, Loel;->t:Ljava/lang/String;

    # Check if Northern Fog Corridor (NDLS / Delhi)
    if-eqz v0, :cond_check_delhi_name
    const-string v3, "NDLS"
    invoke-virtual {v0, v3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v3
    if-eqz v3, :cond_check_delhi_name
    goto :banner_fog

    :cond_check_delhi_name
    if-eqz v1, :cond_check_central
    const-string v3, "Delhi"
    invoke-virtual {v1, v3}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v3
    if-eqz v3, :cond_check_central

    :banner_fog
    if-eqz v2, :cond_fog_default
    new-instance v0, Ljava/lang/StringBuilder;
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V
    const-string v1, "GATI-SETU Fog Cap (60 km/h) | "
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0

    :cond_fog_default
    const-string v0, "GATI-SETU: Fog Safety Cap (60 km/h) to NDLS"
    return-object v0

    # Check if Central / Howrah / Bhusaval / Pune Corridor
    :cond_check_central
    if-eqz v0, :cond_check_central_name
    const-string v3, "HWH"
    invoke-virtual {v0, v3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v3
    if-nez v3, :cond_banner_central
    const-string v3, "BSL"
    invoke-virtual {v0, v3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v3
    if-nez v3, :cond_banner_central
    const-string v3, "PUNE"
    invoke-virtual {v0, v3}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v3
    if-eqz v3, :cond_check_central_name
    goto :banner_central

    :cond_check_central_name
    if-eqz v1, :cond_banner_generic
    const-string v3, "Howrah"
    invoke-virtual {v1, v3}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v3
    if-nez v3, :cond_banner_central
    const-string v3, "Bhusaval"
    invoke-virtual {v1, v3}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v3
    if-nez v3, :cond_banner_central
    const-string v3, "Pune"
    invoke-virtual {v1, v3}, Ljava/lang/String;->contains(Ljava/lang/CharSequence;)Z
    move-result v3
    if-eqz v3, :cond_banner_generic

    :cond_banner_central
    :banner_central
    if-eqz v2, :cond_central_default
    new-instance v0, Ljava/lang/StringBuilder;
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V
    const-string v1, "GATI-SETU Physics | "
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0

    :cond_central_default
    const-string v0, "GATI-SETU: Single-Line & Headway Physics Active"
    return-object v0

    # Default / Generic
    :cond_banner_generic
    :banner_generic
    if-eqz v2, :cond_generic_default
    new-instance v0, Ljava/lang/StringBuilder;
    invoke-direct {v0}, Ljava/lang/StringBuilder;-><init>()V
    const-string v1, "GATI-SETU Dynamic Engine | "
    invoke-virtual {v0, v1}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0, v2}, Ljava/lang/StringBuilder;->append(Ljava/lang/String;)Ljava/lang/StringBuilder;
    invoke-virtual {v0}, Ljava/lang/StringBuilder;->toString()Ljava/lang/String;
    move-result-object v0
    return-object v0

    :cond_generic_default
    const-string v0, "GATI-SETU: Dynamic Physics ETA Active"
    return-object v0
.end method
