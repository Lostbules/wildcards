#!/bin/bash
# categorize.sh — 将 danbooru_general.csv 按 16 个子类自动分类
# 策略: 组件词匹配 + 后缀/前缀规则 + 精确全词匹配
# 数据源: ../danbooru_general.csv (24,317条)
# 产出: ~/.claude/skills/tag-crafter/tag-library/categorized/
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TAGS_DIR="$(dirname "$SCRIPT_DIR")"
INPUT="$TAGS_DIR/danbooru_general.csv"
OUTPUT_DIR="$HOME/.claude/skills/tag-crafter/tag-library/categorized"

echo "=== Danbooru Tag Categorization v4 ==="
echo "Input:  $INPUT"
echo "Output: $OUTPUT_DIR"
echo ""

rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"
for c in subjects body_parts clothing poses expressions composition \
         lighting scenes objects style actions sex_acts body_traits \
         text_features audio_features other; do
  touch "$OUTPUT_DIR/${c}.csv"
done

awk -F',' -v outdir="$OUTPUT_DIR" '
# ================================================================
# 工具: 检查 tag 的组件词中是否有命中词表的
# ================================================================
function has_any(words, wc, dict) {
  for (i = 1; i <= wc; i++) if (words[i] in dict) return 1
  return 0
}

# ================================================================
# 初始化 — 精简但覆盖广的关键词表
# ================================================================
BEGIN {
  # --- subjects (30) ---
  n=split("solo,solo_focus,no_humans,no_human,multiple_girls,multiple_boys,male_focus,female_focus,1girl,1boy,2girls,2boys,3girls,3boys,4girls,4boys,5girls,5boys,6+girls,6+boys,couple,siblings,twins,triplets",A,","); for(i=1;i<=n;i++) D_SUBJECTS[A[i]]

  # --- sex_acts (120) ---
  n=split("sex,anal,vaginal,fellatio,cunnilingus,irrumatio,deepthroat,facesitting,paizuri,footjob,handjob,masturbation,fingering,missionary,cowgirl,doggystyle,spooning,threesome,gangbang,group_sex,foursome,orgy,harem,ahegao,cum,ejaculation,creampie,bukkake,facial,tentacle_sex,machine_sex,bondage,bdsm,restrained,gagged,blindfold,shibari,bound,tied_up,cuffed,handcuffed,chained,rape,molestation,groping,forced,dildo,vibrator,sex_toy,condom,butt_plug,anal_beads,69,penetration,exhibitionism,voyeurism,public_sex,public_nudity,peeping,upskirt,pantyshot,incest,bestiality,necrophilia,oral,erection,erect,hetero,yuri,yaoi,shota,lolicon,naked,nude,completely_nude,topless,bottomless,undressing,undressed,stripping,stripped,disrobing,clothed_sex,cfnm,cmnf,covered_nipples,covered_genitals,covering_breasts,covering_privates,hand_bra,after_sex,post-coital,cuddling,breasts_out,sex_from_behind,girl_on_top,from_behind_position,reverse_cowgirl,double_penetration,triple_penetration,monster_sex,mind_control,brainwashing,cumdrip,cum_drip,cum_leaking,cum_on_face,cum_on_body,cum_in_mouth,cum_in_pussy,cum_in_ass,clothed_female_nude_male,clothed_male_nude_female,half-naked,half_naked",A,","); for(i=1;i<=n;i++) D_SEX[A[i]]

  # --- body_parts: 核心身体词根 (150) ---
  n=split("breast,breasts,nipple,nipples,areola,areolae,underboob,sideboob,underbust,navel,bellybutton,belly,stomach,midriff,abdomen,abs,abdominal,armpit,armpits,hip,hips,waist,thigh,thighs,calf,calves,knee,knees,elbow,elbows,shoulder,shoulders,collarbone,clavicle,hand,hands,finger,fingers,thumb,index_finger,middle_finger,pinky,fingernail,fingernails,foot,feet,toe,toes,toenail,toenails,heel,heels,sole,soles,ankle,ankles,leg,legs,arm,arms,wrist,wrists,head,face,forehead,cheek,cheeks,chin,jaw,jawline,neck,nape,back,spine,torso,chest,pectoral,pectorals,groin,crotch,pubic,pubes,pelvis,pelvic,genital,genitalia,penis,phallus,testicle,testicles,balls,scrotum,pussy,vagina,vulva,clitoris,clit,labia,anus,anal,ass,butt,buttock,buttocks,rear,glutes,tongue,lips,lip,mouth,teeth,tooth,fang,fangs,nose,ear,ears,eyelid,eyelids,eyelash,eyelashes,eyebrow,eyebrows,eye,eyes,pupil,pupils,sclera,iris,tail,tails,wing,wings,horn,horns,claw,claws,paw,paws,hoof,hooves,feather,feathers,fin,fins,scale,scales,fur,skin,tentacle,tentacles,blood,saliva,drool,sweat,tear,tears,vein,veins,muscle,muscles",A,","); for(i=1;i<=n;i++) D_BODYP[A[i]]

  # --- clothing: 服装/鞋/帽/配饰 (200) ---
  n=split("dress,skirt,shirt,blouse,pants,jeans,trousers,shorts,jacket,coat,sweater,vest,blazer,cardigan,pullover,sweatshirt,hoodie,tshirt,tank_top,camisole,crop_top,tube_top,halter,bra,bikini,swimsuit,swimwear,leotard,bodysuit,bodystocking,underwear,underpants,panties,panty,thong,briefs,boxers,lingerie,corset,bustier,stockings,socks,thighhighs,kneehighs,pantyhose,tights,fishnets,leggings,footwear,shoes,boots,heels,sandals,slippers,loafers,sneakers,moccasins,mary_janes,flipflops,hat,cap,beret,beanie,helmet,headwear,headgear,headband,hairband,hairclip,hairpin,hair_ornament,hair_ribbon,hair_bow,hair_flower,hair_tie,hair_band,scrunchie,gloves,glove,scarf,shawl,wrap,stole,boa,cape,cloak,robe,poncho,kimono,yukata,hakama,serafuku,apron,tabard,tunic,toga,veil,crown,tiara,circlet,diadem,necklace,earrings,bracelet,anklet,ring,brooch,badge,patch,armband,wristband,mask,eyewear,glasses,goggles,sunglasses,visor,eyepatch,belt,suspenders,garter,holster,harness,armor,armour,pauldron,gauntlet,greave,cuirass,chainmail,shield,bracer,capelet,sailor_collar,pendant,cufflinks,tie_clip,handkerchief,ascot,cravat,necktie,bowtie,neckerchief,obi,sash,obi_age,obi_jime,geta,zori,tabi,waraji,okobo",A,","); for(i=1;i<=n;i++) D_CLOTH[A[i]]
  # 服装特征/结构词
  n=split("sleeve,sleeves,sleeveless,collar,collared,neckline,v-neck,v_neck,scoop_neck,turtleneck,off_shoulder,strapless,backless,open_back,open_clothes,open_jacket,detached_sleeves,wide_sleeves,long_sleeves,short_sleeves,puffy_sleeves,frilled_sleeves,bell_sleeves,cap_sleeves,sleeves_past_wrists,sleeves_past_fingers,rolled_up_sleeves,bare_shoulders,bare_arms,bare_legs,bare_back,bare_midriff,bare_stomach,cropped,cutoff,cutoffs,ripped,torn,see-through,see_through,sheer,revealing,cutout,keyhole,side_slit,slit,pleat,pleats,pleated,frills,frill,frilled,ruffles,ruffle,ruffled,lace,laced,lacy,mesh,crochet,knit,knitted,denim,leather,latex,spandex,velvet,silk,satin,fur_trim,fur_trimmed,feather_trim,plaid,flannel,checkered,checked,striped,stripes,polka_dot,dotted,animal_print,floral_print,floral,camo,camouflage,gradient,ombre,multicolored,patchwork,quilted,embroidered,embroidery,beaded,sequin,rhinestone,studded,spiked,zipper,buttons,button,buckle,buckles,strap,straps,lace-up,cross-laced,ribbon,ribbons,bow,bows,trim,trimmed,hem,hemline,ruche,ruching,gather,gathers,shirr,shirring",A,","); for(i=1;i<=n;i++) D_CLOTH_FEAT[A[i]]

  # --- poses (100) ---
  n=split("stand,stands,standing,stood,sit,sits,sitting,seated,kneel,kneels,kneeling,knelt,squat,squats,squatting,crouch,crouches,crouching,lie,lies,lying,lay,lain,recline,reclines,reclining,lean,leans,leaning,bend,bends,bending,bent,stoop,stoops,stooping,slouch,slouches,slouching,slump,slumps,slumping,sprawl,sprawls,sprawling,lounge,lounges,lounging,stretch,stretches,stretching,reach,reaches,reaching,all_fours,bent_over,spread_legs,leg_spread,legs_apart,legs_together,crossed_legs,leg_cross,leg_crossing,lotus_position,indian_style,seiza,wariza,yokozuwari,handstand,headstand,shoulderstand,on_back,on_stomach,on_side,on_belly,facedown,faceup,face_down,face_up,upside_down,inverted,arched_back,back_arch,backbend,contrapposto,fighting_stance,dynamic_pose,action_pose,hand_on_hip,hands_on_hips,hand_on_knee,hands_on_knees,hands_behind_back,hands_behind_head,arms_behind_back,arms_behind_head,arms_crossed,crossed_arms,arms_up,arms_outstretched,outstretched_arms",A,","); for(i=1;i<=n;i++) D_POSE[A[i]]

  # --- expressions (80) ---
  n=split("smile,smiles,smiling,grin,grins,grinning,frown,frowns,frowning,scowl,scowls,scowling,glare,glares,glaring,pout,pouts,pouting,sneer,sneers,sneering,grimace,grimaces,grimacing,wince,winces,wincing,snarl,snarls,snarling,cry,cries,crying,weep,weeps,weeping,sob,sobs,sobbing,wail,wails,wailing,blush,blushing,flush,flushed,nosebleed,anger_vein,sweatdrop,sweat,sweating,tremble,trembling,shake,shaking,shiver,shivering,quiver,quivering,shudder,shuddering,look,looks,looking,gaze,gazes,gazing,stare,stares,staring,glance,glances,glancing,peer,peers,peering,open_mouth,closed_mouth,open_eyes,closed_eyes,wide_eyed,one_eye_closed,narrowed_eyes,rolling_eyes,empty_eyes,blank_eyes,heart_eyes,star_eyes,dilated_pupils,constricted_pupils,bright_pupils,slit_pupils,sparkling_eyes,glowing_eyes,tears,teary,tearful,tearing_up,crying_with_eyes_open,parted_lips,licking_lips,biting_lip,tongue_out,drool,drooling,lick,licks,licking,bite,bites,biting",A,","); for(i=1;i<=n;i++) D_EXPR[A[i]]

  # --- composition (60) ---
  n=split("from_above,from_below,aerial_view,dutch_angle,fisheye,front_view,side_view,back_view,rear_view,turned_back,profile,full_body,cowboy_shot,cropped_legs,cropped_arms,close-up,close_up,upper_body,lower_body,head_shot,bust_shot,waist_up,knees_up,selfie,multiple_views,pov,first-person_view,first_person_view,foreshortening,wide_shot,long_shot,medium_shot,extreme_closeup,depth_of_field,bokeh,foreground_blur,background_blur,blurry,blur,phone_screen_framing,shaky_handheld,rule_of_thirds,symmetry,asymmetry,leading_lines,golden_ratio,vignette,vignetting,border,white_border,black_border,framed,framing,low_angle,high_angle,eye_level,bird_eye_view,overhead_view,panorama,landscape,portrait,square_format,hand_up,arm_up,feet_out_of_frame,out_of_frame,outside_border,head_tilt,arm_support,motion_lines,emphasis_lines,speed_lines,action_lines,motion_blur,cover_page",A,","); for(i=1;i<=n;i++) D_COMP[A[i]]

  # --- lighting (80) ---
  n=split("sunlight,sunbeam,sunbeams,backlighting,backlight,backlit,moonlight,moonbeam,moonbeams,chiaroscuro,silhouette,cinematic_lighting,soft_light,soft_lighting,harsh_light,harsh_lighting,lens_flare,god_rays,rim_lighting,rim_light,light_particles,against_light,crepuscular_rays,light_rays,night,day,sunset,sunrise,dusk,dawn,twilight,evening,morning,noon,midday,afternoon,midnight,shadow,shadows,shade,shading,shaded,reflection,reflections,reflective,shiny,shimmer,gloss,glossy,glow,glowing,gleam,gleaming,glint,glisten,glistening,glitter,glittering,sparkle,sparkling,twinkle,twinkling,radiant,radiance,luminous,luminescence,fog,mist,misty,haze,hazy,smog,rain,rainfall,raining,rainy,drizzle,snow,snowfall,snowing,snowy,sleet,hail,storm,stormy,blizzard,lightning,thunder,thunderstorm,wind,windy,breeze,breezy,overcast,cloudy,rainbow,aurora,starry_sky,night_sky,blue_sky,cloudy_sky,warm_light,cool_light,candlelight,firelight,neon,neon_lights,dark,darkness,dim,bright,wet,moist,damp,humid,steam,steamy,smoke,smoky,fire,flame,flames,blaze,blazing,burn,burning,embers,ash,ashes",A,","); for(i=1;i<=n;i++) D_LIGHT[A[i]]

  # --- scenes (100) ---
  n=split("bedroom,classroom,bathroom,living_room,kitchen,dining_room,hallway,locker_room,outdoors,indoors,beach,city,rooftop,school,office,gym,stadium,park,street,forest,garden,pool,train,bus,car,airplane,airport,ship,boat,cafe,restaurant,library,hospital,hotel,temple,shrine,church,mosque,cathedral,building,room,doorway,window,balcony,stairs,staircase,hall,corridor,sky,cloud,clouds,ocean,sea,river,lake,mountain,volcano,cave,island,countryside,farm,barn,market,marketplace,plaza,alley,alleyway,sidewalk,pier,dock,amusement_park,aquarium,zoo,museum,theater,cinema,concert,festival,fair,circus,playground,field,meadow,desert,snowscape,underwater,swamp,jungle,waterfall,grassland,prairie,savanna,tundra,steppe,valley,canyon,gorge,ravine,cliff,tree,plant,grass,flower,flowers,wood,woods,forest,rainforest,on_bed,on_floor,on_ground,on_grass,in_water,in_pool,in_bath,in_shower",A,","); for(i=1;i<=n;i++) D_SCENE[A[i]]

  # --- objects (150) ---
  n=split("sword,gun,weapon,shield,knife,spear,bow,arrow,dagger,axe,hammer,staff,wand,rifle,pistol,shotgun,cannon,blade,katana,rapier,saber,cutlass,scimitar,falchion,broadsword,longsword,shortsword,greatsword,claymore,bokken,shinai,lightsaber,book,phone,smartphone,cellphone,mobile_phone,telephone,food,drink,cup,plate,fork,spoon,bowl,chopsticks,bottle,mug,glass,teacup,saucer,teapot,pitcher,jug,wine_glass,champagne_flute,flower,rose,microphone,camera,bag,backpack,umbrella,parasol,fan,musical_instrument,guitar,piano,violin,flute,drum,trumpet,saxophone,clarinet,oboe,bassoon,french_horn,trombone,tuba,chair,table,desk,bed,couch,sofa,ottoman,footstool,stool,bench,throne,pillow,blanket,mirror,lamp,candle,clock,vase,painting,picture_frame,poster,ball,doll,teddy_bear,toy,plushie,stuffed_toy,computer,laptop,keyboard,mouse,screen,monitor,tv,television,tablet,headphones,earphones,speaker,heart,star,halo,bell,petal,petals,fruit,bird,leaf,leaves,tree,branch,twig,blossom,bloom,bud,seed,vine,ring,gem,jewel,rope,box,candy,gift,present,cake,fish,alcohol,tray,broom,cigarette,cigar,pipe,hookah,bong,vape,instrument",A,","); for(i=1;i<=n;i++) D_OBJ[A[i]]

  # --- style (60) ---
  n=split("monochrome,greyscale,grayscale,sketch,lineart,watercolor,oil_painting,acrylic,pastel,gouache,tempera,encaustic,fresco,mural,mosaic,collage,digital_art,digital_painting,digital_drawing,digital_illustration,traditional_media,traditional_art,traditional_painting,traditional_drawing,absurdres,highres,lowres,bad_id,tagme,very_high_resolution,simple_background,white_background,grey_background,gray_background,transparent_background,gradient_background,black_background,blue_background,red_background,green_background,pink_background,purple_background,yellow_background,brown_background,simple_shading,flat_color,cel_shading,gradient_shading,soft_shading,photorealistic,realistic,3d,2d,anime,cartoon,manga,comic,chibi,pixel_art,vector,vector_art,mixed_media,official_art,fanart,fan_art,doujinshi,fan_fiction,parody,clean_lines,thick_lines,thin_lines,sketchy,rough,polished,detailed,highly_detailed,censored,uncensored,mosaic_censoring,bar_censor,heart_censor,star_censor,convenient_censoring,spot_color,outline,outlined,silhouette,colorful,multicolored",A,","); for(i=1;i<=n;i++) D_STYLE[A[i]]

  # --- actions (120) ---
  n=split("hold,holds,holding,held,carry,carries,carrying,carried,eat,eats,eating,ate,drink,drinks,drinking,drank,read,reads,reading,write,writes,writing,wrote,draw,draws,drawing,drew,paint,paints,painting,painted,sketch,sketches,sketching,sketched,run,runs,running,ran,walk,walks,walking,walked,jump,jumps,jumping,jumped,dance,dances,dancing,danced,fly,flies,flying,flew,swim,swims,swimming,swam,crawl,crawls,crawling,crawled,hop,hops,hopping,hopped,skip,skips,skipping,skipped,fight,fights,fighting,fought,punch,punches,punching,punched,kick,kicks,kicking,kicked,grab,grabs,grabbing,grabbed,pull,pulls,pulling,pulled,push,pushes,pushing,pushed,throw,throws,throwing,threw,swing,swings,swinging,swung,slash,slashes,slashing,slashed,block,blocks,blocking,blocked,hug,hugs,hugging,hugged,kiss,kisses,kissing,kissed,touch,touches,touching,touched,caress,caresses,caressing,caressed,stroke,strokes,stroking,stroked,pet,pets,petting,petted,pat,pats,patting,patted,tickle,tickles,tickling,tickled,sleep,sleeps,sleeping,slept,rest,rests,resting,rested,wait,waits,waiting,waited,hide,hides,hiding,hid,peek,peeks,peeking,peeked,point,points,pointing,pointed,wave,waves,waving,waved,salute,salutes,saluting,saluted,bow,bows,bowing,bowed,pray,prays,praying,prayed,beg,begs,begging,begged,plead,pleads,pleading,pleaded,lift,lifts,lifting,lifted,catch,catches,catching,caught,drop,drops,dropping,dropped,open,opens,opening,opened,close,closes,closing,closed,pour,pours,pouring,poured,sweep,sweeps,sweeping,swept,wash,washes,washing,washed,clean,cleans,cleaning,cleaned,cook,cooks,cooking,cooked,bake,bakes,baking,baked,sing,sings,singing,sang,speak,speaks,speaking,spoke,shout,shouts,shouting,shouted,whisper,whispers,whispering,whispered,yell,yells,yelling,yelled,scream,screams,screaming,screamed,laugh,laughs,laughing,laughed,giggle,giggles,giggling,giggled,straddle,straddles,straddling,mount,climb,climbs,climbing",A,","); for(i=1;i<=n;i++) D_ACT[A[i]]

  # --- body_traits: 精确全词匹配 ---
  n=split("blonde_hair,brown_hair,black_hair,red_hair,blue_hair,green_hair,pink_hair,purple_hair,white_hair,grey_hair,silver_hair,orange_hair,blue_eyes,brown_eyes,green_eyes,red_eyes,yellow_eyes,purple_eyes,pink_eyes,black_eyes,grey_eyes,white_eyes,heterochromia,multicolored_hair,two-tone_hair,streaked_hair,gradient_hair,split_color_hair,very_long_hair,short_hair,medium_hair,long_hair,very_short_hair,buzz_cut,shaved_head,twintails,ponytail,braid,bun,sidelocks,bangs,hair_between_eyes,side_ponytail,low_twintails,high_twintails,braided_ponytail,double_bun,single_braid,twin_braids,french_braid,pigtails,hime_cut,bob_cut,pixie_cut,undercut,asymmetrical_hair,blunt_bangs,parted_bangs,swept_bangs,crossed_bangs,small_breasts,medium_breasts,large_breasts,huge_breasts,gigantic_breasts,flat_chest,no_breasts,muscular,athletic,slim,chubby,plump,fat,overweight,obese,skinny,thin,curvy,hourglass,pear-shaped,tall,short,petite,loli,lolita,shota,bara,otoko_no_ko,futanari,newhalf,shemale,transgender,transsexual,crossdresser,tomboy,tomgirl,femboy,androgynous,kemonomimi,nekomimi,inumimi,usamimi,v-shaped_eyebrows,thick_eyebrows,thin_eyebrows,tsurime,tareme,jitome,sanpaku,colored_sclera,black_sclera,white_pupils,slit_pupils,heart-shaped_pupils,symbol-shaped_pupils,dark-skinned_female,dark-skinned_male,dark_skinned_female,dark_skinned_male,pale_skin,dark_skin,tan,tanlines,skindentation,thigh_gap,cameltoe,freckles,mole,scar,tattoo,birthmark,beauty_mark,dimples,animal_ear_fluff,mole_under_eye,nose_blush,ahoge,fang,elf,elf_ears,pointy_ears,cat_ears,animal_ears,dog_ears,fox_ears,bunny_ears,sharp_teeth,muscular_male,mature_male,mature_female,horse_girl,cat_girl,fox_girl,dog_girl,bunny_girl,rabbit_girl,wolf_girl,demon_girl,monster_girl,dragon_girl,slime_girl,robot_girl,alien_girl,elf_girl,vampire_girl,zombie_girl,ghost_girl,angel_girl,devil_girl,succubus_girl,incubus_boy,mermaid,merman,centaur,harpy,minotaur,satyr,faun,lamia,naga,kitsune,nekomata,bakeneko,tanuki,oni,tengu,kappa,werewolf,lycan,lycanthrope,werecat,werefox,werebear,weretiger,zombie,ghoul,undead,skeleton,lich,wraith,phantom,ghost,spirit,poltergeist,vampire,android,cyborg,robot,mecha,alien,humanoid,anthro,furry,slime,elemental,gorgon,medusa,cyclops,kraken,yeti,bigfoot,goblin,orc,ogre,troll,giant,dwarf,gnome,fairy,faerie,pixie,sprite,nymph,dryad,hobbit,halfling,mutant,yokai,ayakashi,kaiju,esper,psychic",A,","); for(i=1;i<=n;i++) D_BT_EXACT[A[i]]

  # --- text_features (40) ---
  n=split("speech_bubble,thought_bubble,scream_bubble,dialogue_bubble,text_bubble,action_bubble,english_text,japanese_text,chinese_text,korean_text,translated_text,text,signature,watermark,twitter_username,pixiv_id,artist_name,copyright_notice,url,website,translation_request,commentary_request,source_request,dialogue,monologue,text_focus,screen_text,ui,user_interface,speech,letter,letterboxed,logo,brand,trademark,spoken_heart,spoken_ellipsis,web_address,patreon_username,character_name,copyright_name,chat,chat_message,text_message",A,","); for(i=1;i<=n;i++) D_TEXT[A[i]]

  # --- audio_features (10) ---
  n=split("sfx,sound_effects,onomatopoeia,sound,sound_effect,sound_effect_text,audio,music,musical_note,musical_notes",A,","); for(i=1;i<=n;i++) D_AUDIO[A[i]]

  # 计数器
  split("subjects,body_parts,clothing,poses,expressions,composition,lighting,scenes,objects,style,actions,sex_acts,body_traits,text_features,audio_features,other",cats_arr,",")
  for(i in cats_arr) counts[cats_arr[i]]=0
  total=0; matched_tags=0
}

# ================================================================
# 主处理
# ================================================================
{
  tag = $1; line = $0; total++
  wc = split(tag, words, "_"); hit = 0

  # 辅助函数: 任一组分词命中
  # (在行内使用 for 循环)

  # --- 1. subjects ---
  if (tag in D_SUBJECTS || tag ~ /^[0-9]+\+?(girls?|boys?|others?)$/) {
    print line >> outdir "/subjects.csv"; counts["subjects"]++; hit=1
  }

  # --- 12. sex_acts (高优先级, 防止污染 poses/actions) ---
  sx=0; for(i=1;i<=wc;i++) if(words[i] in D_SEX) {sx=1;break}
  if(!sx && tag ~ /_sex$|_sex_|^sex_|_rape$|_molest|_grop|_forced|_bondage|_bdsm|_dildo|_vibrator|_penetration|_job$|_position$|_creampie$|_bukkake$|_facial$|_cum$|_cum_|^cum_|_ahegao$|_ejaculation|_oral$|_erection|_naked$|_nude$|_topless$|_bottomless$|_exhibitionism|_voyeurism|_peeping|_upskirt|_pantyshot|_incest|_bestiality|_necrophilia|_zoophilia/) sx=1
  if(!sx && tag ~ /^(naked|nude|completely_nude|topless|bottomless|half-naked|half_naked|undressing|undressed|stripping|stripped|disrobing|clothed_sex|cfnm|cmnf|after_sex|post-coital|cuddling|breasts_out|covered_nipples|covered_genitals|covering_breasts|covering_privates|hand_bra)$/) sx=1
  if(sx) { print line >> outdir "/sex_acts.csv"; counts["sex_acts"]++; hit=1 }

  # --- 5. expressions ---
  ex=0; for(i=1;i<=wc;i++) if(words[i] in D_EXPR) {ex=1;break}
  if(!ex && tag ~ /^(looking_|facing_|eye_contact|averting_eyes|:d|:p|:o|:q|;\)|;\(|>:\\(|>;\\)|>_<|@_@|o_o|t_t|>_>|\^_\^|\^\^|\^\^;|:3|;d|:<|;p|<3|<\/3)$/) ex=1
  if(!ex && tag ~ /^tears_/) ex=1
  if(ex) { print line >> outdir "/expressions.csv"; counts["expressions"]++; hit=1 }

  # --- 6. composition ---
  cp=0; for(i=1;i<=wc;i++) if(words[i] in D_COMP) {cp=1;break}
  if(!cp && tag ~ /_(view|shot|angle|closeup|close-up|close_up|bokeh|blur|vignette|framing|composition)$/) cp=1
  if(!cp && tag ~ /_out_of_frame$|_outside_border$|motion_lines$|emphasis_lines$|speed_lines$|action_lines$|movement_lines$|motion_blur$/) cp=1
  if(cp) { print line >> outdir "/composition.csv"; counts["composition"]++; hit=1 }

  # --- 7. lighting ---
  lg=0; for(i=1;i<=wc;i++) if(words[i] in D_LIGHT) {lg=1;break}
  if(!lg && tag ~ /_(light|lighting|lights|rays|beam|beams|shine|glow|sparkle|twinkle|flare|shimmer|radiance|luminescence|illumination)$/) lg=1
  if(!lg && tag ~ /^(rain|rainy|raining|snow|snowing|snowy|fog|foggy|mist|misty|haze|hazy|overcast|storm|stormy|thunder|lightning|wind|windy|breeze|breezy|wet|moist|damp|humid|steam|steamy|smoke|smoky)$/) lg=1
  if(lg) { print line >> outdir "/lighting.csv"; counts["lighting"]++; hit=1 }

  # --- 4. poses ---
  ps=0; for(i=1;i<=wc;i++) if(words[i] in D_POSE) {ps=1;break}
  if(!ps && tag ~ /_pose$|_position$|_stance$|_posture$/) ps=1
  if(!ps && tag ~ /^(all_fours|bent_over|on_back|on_stomach|on_side|on_belly|facedown|faceup|upside_down|arched_back|backbend|contrapposto|fighting_stance|dynamic_pose|action_pose|hand_on_hip|hands_on_hips|hands_behind_back|hands_behind_head|arms_behind_back|arms_behind_head|arms_crossed|crossed_arms|arms_up|arms_outstretched|outstretched_arms|handstand|headstand|shoulderstand|splits|doing_splits)$/) ps=1
  if(ps) { print line >> outdir "/poses.csv"; counts["poses"]++; hit=1 }

  # --- 11. actions ---
  ac=0; for(i=1;i<=wc;i++) if(words[i] in D_ACT) {ac=1;break}
  if(!ac && tag ~ /^(holding_|carrying_|eating_|drinking_|reading_|writing_|drawing_|painting_|sketching_|running_|walking_|jumping_|dancing_|flying_|swimming_|climbing_|crawling_|hopping_|skipping_|fighting_|punching_|kicking_|grabbing_|pulling_|pushing_|throwing_|swinging_|slashing_|blocking_|hugging_|kissing_|touching_|caressing_|stroking_|petting_|patting_|tickling_|sleeping_|resting_|waiting_|hiding_|peeking_|pointing_|waving_|saluting_|bowing_|praying_|begging_|pleading_|lifting_|catching_|dropping_|opening_|closing_|pouring_|sweeping_|washing_|cleaning_|cooking_|baking_|singing_|speaking_|shouting_|whispering_|yelling_|screaming_|laughing_|giggling_|straddling_|mounting_|dismounting_|boarding_|taking_photo$|using_phone$|typing$|playing_)/) ac=1
  if(!ac && tag ~ /_lift$|_pull$|_push$|_grab$|_throw$|_catch$|_drop$|_clothes_lift$|clothes_lift$|_clothes_pull$|clothes_pull$/) ac=1
  if(ac) { print line >> outdir "/actions.csv"; counts["actions"]++; hit=1 }

  # --- 8. scenes ---
  sc=0; for(i=1;i<=wc;i++) if(words[i] in D_SCENE) {sc=1;break}
  if(!sc && tag ~ /_(room|rooms|shop|shops|store|stores|station|stations|school|schools|building|buildings|scape|scapes|landscape|landscapes|environment|environments|setting|settings|location|locations|venue|venues|interior|interiors|exterior|exteriors|indoors|outdoors|background|backgrounds|backdrop|backdrops)$/) sc=1
  if(!sc && tag ~ /^(on_bed|on_floor|on_ground|on_grass|on_sand|in_water|underwater|in_pool|in_bath|in_shower|in_tub|in_sky|in_air|in_space)$/) sc=1
  if(sc) { print line >> outdir "/scenes.csv"; counts["scenes"]++; hit=1 }

  # --- 3. clothing ---
  cl=0; for(i=1;i<=wc;i++) if(words[i] in D_CLOTH) {cl=1;break}
  if(!cl) { for(i=1;i<=wc;i++) if(words[i] in D_CLOTH_FEAT) {cl=1;break} }
  if(!cl && tag ~ /_(clothes|clothing|garment|garments|apparel|attire|outfit|ensemble|wear|wears|uniform|costume|dress|skirt|shirt|blouse|pants|jeans|trousers|shorts|socks|stockings|tights|leggings|shoes|boots|sandals|slippers|heels|footwear|legwear|hat|cap|beret|helmet|hood|jacket|coat|sweater|vest|blazer|cardigan|pullover|sweatshirt|hoodie|tshirt|camisole|corset|leotard|bodysuit|swimsuit|swimwear|bikini|underwear|panties|bra|lingerie|apron|gloves|glove|scarf|shawl|wrap|stole|boa|cape|cloak|robe|poncho|kimono|yukata|hakama|serafuku|necklace|earrings|bracelet|ring|brooch|badge|patch|armband|wristband|headband|hairband|hairclip|hairpin|hair_ornament|hair_ribbon|hair_bow|hair_flower|hair_tie|hair_band|hairstick|hair_accessory|hair_decorations|tiara|crown|circlet|diadem|veil|mask|eyewear|glasses|goggles|sunglasses|visor|eyepatch|belt|suspenders|garter|holster|harness|armor|armour|pauldron|gauntlet|greave|cuirass|chainmail|shield|bracer|capelet|sailor_collar|capelet|brooch|pendant|cufflinks|tie_clip|pocket_square|handkerchief|ascot|cravat)$/) cl=1
  if(!cl && tag ~ /^hair_ornament|^hair_ribbon|^hair_bow|^hair_clip|^hair_flower|^hair_tie|^hair_band|^hairband|^hairclip|^hairpin|^hair_pin|^hairstick/) cl=1
  if(!cl && tag ~ /_piercing$|_piercings$|^nail_polish$|_nails$|^nail_/) cl=1
  if(!cl && tag ~ /^(frills|frill|lace|ribbon|bows|trim|trimmed|armor|armour|chainmail|plate_mail)$/) cl=1
  if(cl) { print line >> outdir "/clothing.csv"; counts["clothing"]++; hit=1 }

  # --- 9. objects ---
  ob=0; for(i=1;i<=wc;i++) if(words[i] in D_OBJ) {ob=1;break}
  if(!ob && tag ~ /_(sword|gun|weapon|shield|knife|spear|bow|arrow|dagger|axe|hammer|staff|wand|rifle|pistol|shotgun|cannon|blade|katana|rapier|saber|scimitar|falchion|broadsword|longsword|shortsword|greatsword|claymore|book|phone|food|drink|cup|plate|fork|spoon|bowl|bottle|mug|glass|teacup|saucer|teapot|flower|rose|microphone|camera|bag|backpack|umbrella|parasol|fan|guitar|piano|violin|flute|drum|trumpet|saxophone|clarinet|oboe|bassoon|french_horn|trombone|tuba|chair|table|desk|bed|couch|sofa|stool|bench|throne|pillow|blanket|mirror|lamp|candle|clock|vase|painting|picture|poster|ball|doll|toy|plushie|teddy_bear|computer|laptop|keyboard|mouse|screen|monitor|tv|television|tablet|headphones|earphones|speaker|record|cd|dvd|cassette|tape|projector|heart|star|bell|petal|fruit|bird|leaf|branch|blossom|bloom|bud|seed|vine|ring|gem|jewel|rope|box|candy|gift|cake|fish|alcohol|tray|broom|cigarette|cigar|pipe|instrument|musical_instrument)$/) ob=1
  if(!ob && tag ~ /^holding_/) ob=1
  if(ob) { print line >> outdir "/objects.csv"; counts["objects"]++; hit=1 }

  # --- 2. body_parts ---
  bp=0; for(i=1;i<=wc;i++) if(words[i] in D_BODYP) {bp=1;break}
  if(bp) { print line >> outdir "/body_parts.csv"; counts["body_parts"]++; hit=1 }

  # --- 13. body_traits ---
  bt=0
  if(tag in D_BT_EXACT) bt=1
  if(!bt && tag ~ /_hair$/) {
    # 排除发饰(由clothing处理): hair_ornament, hair_ribbon, hair_bow, hair_clip, hair_flower, hair_tie, hair_band, hair_accessory
    if(tag !~ /^hair_ornament|^hair_ribbon|^hair_bow|^hair_clip|^hair_flower|^hair_tie|^hair_band|^hair_accessory|^hair_decorations|^hair_ornaments|^hairpin|^hair_pin|^hairpins|^hairstick|^hairsticks$/) bt=1
  }
  if(!bt && tag ~ /_eyes$/) bt=1
  if(!bt && tag ~ /_(skin|tan|breasts|chest|build|body|muscular|athletic|slim|fat|chubby|plump|tattoo|tattoos|pupils|pupil|sclera|ears|tail|tails|horn|horns|wings|claws|fang|fangs|tusk|tusks|fur|scales|feathers|feather|fin|fins|gill|gills)$/) bt=1
  if(!bt && tag ~ /^(dark|pale|fair|light|tan|brown|olive)_(skinned|skin)/) bt=1
  if(!bt && tag ~ /^colored_sclera|_pupils$|_pupil$|_sclera$/) bt=1
  if(!bt && tag ~ /_girl$|_boy$|_male$|_female$|_man$|_woman$/) {
    # cat_girl, fox_boy etc.
    if(tag ~ /^(cat|dog|fox|wolf|bunny|rabbit|horse|cow|sheep|deer|bear|bird|owl|snake|lizard|dragon|shark|fish|dolphin|octopus|spider|butterfly|frog|turtle|bat|mouse|rat|hamster|ferret|otter|seal|penguin|duck|swan|monster|demon|angel|devil|succubus|incubus|fairy|mermaid|centaur|harpy|minotaur|satyr|lamia|naga|kitsune|bakeneko|tanuki|oni|tengu|kappa|vampire|werewolf|zombie|ghost|spirit|slime|robot|mecha|alien|elf)_(girl|boy|male|female|man|woman)$/) bt=1
  }
  if(!bt && tag ~ /^(loli|lolita|shota|bara|otoko_no_ko|futanari|newhalf|shemale|transgender|transsexual|crossdresser|tomboy|tomgirl|femboy|androgynous)$/) bt=1
  if(!bt && tag ~ /^(elf|dwarf|orc|goblin|troll|ogre|giant|fairy|faerie|pixie|sprite|nymph|dryad|mermaid|merman|siren|centaur|harpy|minotaur|satyr|faun|lamia|naga|kitsune|bakeneko|tanuki|oni|tengu|kappa|vampire|werewolf|lycan|lycanthrope|werecat|werefox|werebear|weretiger|zombie|ghoul|undead|skeleton|lich|wraith|phantom|ghost|spirit|poltergeist|android|cyborg|robot|mecha|alien|humanoid|anthro|furry|slime|elemental|gorgon|medusa|cyclops|kraken|yeti|bigfoot|goblin|orc|ogre|troll|giant|dwarf|gnome|hobbit|halfling|mutant|yokai|ayakashi)$/) bt=1
  if(!bt && tag ~ /^(freckles|mole|scar|tattoo|birthmark|beauty_mark|dimples|ahoge)$/) bt=1
  if(bt) { print line >> outdir "/body_traits.csv"; counts["body_traits"]++; hit=1 }

  # --- 10. style ---
  st=0; for(i=1;i<=wc;i++) if(words[i] in D_STYLE) {st=1;break}
  if(!st && tag ~ /_(background|shading|art|style|drawing|painting|illustration|sketch|lineart|medium|media|technique)$/) st=1
  if(!st && tag ~ /^(monochrome|greyscale|grayscale|sketch|lineart|absurdres|highres|lowres|bad_id|tagme|censored|uncensored|mosaic_censoring|bar_censor|heart_censor|star_censor|convenient_censoring|spot_color|outline|outlined|silhouette|colorful|multicolored)$/) st=1
  if(!st && tag ~ /^.*_background$/) { if(tag ~ /^(white|black|grey|gray|blue|red|green|pink|purple|yellow|orange|brown|transparent|simple|gradient|plain|solid|colored)_background$/) st=1 }
  if(st) { print line >> outdir "/style.csv"; counts["style"]++; hit=1 }

  # --- 14. text_features ---
  tx=0; for(i=1;i<=wc;i++) if(words[i] in D_TEXT) {tx=1;break}
  if(!tx && tag ~ /_(text|bubble|username|name|signature|watermark|logo|brand|trademark|request|dialogue|monologue|screen|ui|interface|message|notification|menu|bar|popup|window|dialog|alert|overlay|hud)$/) tx=1
  if(tx) { print line >> outdir "/text_features.csv"; counts["text_features"]++; hit=1 }

  # --- 15. audio_features ---
  au=0; for(i=1;i<=wc;i++) if(words[i] in D_AUDIO) {au=1;break}
  if(au) { print line >> outdir "/audio_features.csv"; counts["audio_features"]++; hit=1 }

  # --- SECOND PASS: last-word (head noun) matching ---
  if(!hit && wc > 0) {
    lw = words[wc]  # last component word

    # Clothing by last-word suffix
    if(lw ~ /^(choker|necklace|earrings|bracelet|anklet|ring|brooch|pendant|badge|patch|armband|wristband|headband|hairband|hairclip|hairpin|hair_ornament|hair_ribbon|hair_bow|hair_flower|hair_tie|scrunchie|gauntlet|pauldron|greave|cuirass|chainmail|bracer|capelet|headdress|headgear|headwear|tiara|crown|circlet|diadem|veil|mask|eyewear|glasses|goggles|sunglasses|visor|eyepatch|monocle|belt|suspenders|garter|holster|harness|armor|armour|shield|ascot|cravat|necktie|bowtie|neckerchief|obi|sash|geta|zori|tabi|waraji|okobo|loafers|mary_janes|moccasins|flipflops|sneakers|sandals|slippers|heels|boots|shoes|footwear|legwear|socks|stockings|tights|leggings|pantyhose|fishnets|thighhighs|kneehighs|swimwear|swimsuit|bikini|underwear|panties|bra|lingerie|apron|kimono|yukata|hakama|serafuku|uniform|costume|dress|skirt|shirt|blouse|pants|jeans|trousers|shorts|jacket|coat|sweater|vest|blazer|cardigan|pullover|hoodie|sweatshirt|tshirt|camisole|corset|leotard|bodysuit|tunic|robe|cloak|cape|poncho|toga|kaftan|hijab|niqab|sari|cheongsam|hanfu|hanbok|buruma|bloomers|sarashi|leotard|petticoat|gakuran|sportswear|overalls|pajamas|bandeau|towel|bathrobe|nightgown|yukata|maid|waitress|nurse|cheerleader|miko|nun|maid_uniform|sailor_uniform|school_uniform|military_uniform|japanese_clothes|chinese_clothes|western_clothes|fantasy_clothes|sci-fi_clothes|pom_pom|halterneck|strapless|backless|off_shoulder|turtleneck|v-neck|scoop_neck|sleeveless|miniskirt|microskirt)$/) { print line >> outdir "/clothing.csv"; counts["clothing"]++; hit=1 }

    # Body traits by last-word
    else if(lw ~ /^(hair|eyes|skin|tan|ears|tail|tails|horns|wings|breasts|chest|body|build|pupils|pupil|sclera|fang|fangs|tusk|tusks|claws|fur|scales|feathers|fin|fins|gill|gills|bun|ponytail|braid|braids|bangs|twintails|pigtails|sidelocks|ahoge|forehead|widow_peak|beard|mustache|goatee|sideburns|stubble|dimples|freckles|mole|scar|tattoo|tattoos|birthmark|piercing|piercings|makeup|eyeshadow|eyeliner|lipstick|nail_polish|blush|tanlines|hairstyle|haircut|hair_style|hair_length|hair_color|eye_color|skin_color|body_type|body_shape|breast_size)$/) { print line >> outdir "/body_traits.csv"; counts["body_traits"]++; hit=1 }

    # Expressions by last-word
    else if(lw ~ /^(smile|grin|frown|scowl|glare|pout|sneer|grimace|wince|snarl|cry|weep|sob|wail|blush|blushing|tears|tear|expression|expressions|eyes|eyed|gaze|stare|glance|peer|look|looking|mouth|tongue|lips|lip|biting|licking|drool|drooling|tremble|trembling|shake|shaking|quiver|quivering|sweat|sweating|sweatdrop|nosebleed|anger|vein|emotion|embarrassed|happy|sad|angry|surprised|serious|smug|nervous|shy|scared|frightened|terrified|horrified)$/) { print line >> outdir "/expressions.csv"; counts["expressions"]++; hit=1 }

    # Objects by last-word
    else if(lw ~ /^(sword|gun|weapon|shield|knife|spear|bow|arrow|dagger|axe|hammer|staff|wand|rifle|pistol|shotgun|cannon|blade|katana|rapier|saber|scimitar|falchion|broadsword|longsword|shortsword|greatsword|claymore|book|phone|food|drink|cup|plate|fork|spoon|bowl|chopsticks|bottle|mug|glass|teacup|saucer|teapot|pitcher|jug|flower|rose|microphone|camera|bag|backpack|umbrella|parasol|fan|guitar|piano|violin|flute|drum|trumpet|saxophone|clarinet|oboe|bassoon|trombone|tuba|chair|table|desk|bed|couch|sofa|stool|bench|throne|pillow|blanket|mirror|lamp|candle|clock|vase|painting|picture|poster|ball|doll|toy|plushie|computer|laptop|keyboard|mouse|screen|monitor|tv|television|tablet|headphones|earphones|speaker|heart|star|bell|petal|fruit|bird|leaf|leaves|tree|branch|twig|blossom|bloom|bud|seed|vine|ring|gem|jewel|rope|box|candy|gift|present|cake|fish|alcohol|tray|broom|cigarette|cigar|pipe|hookah|bong|vape|instrument|lantern|bouquet|lollipop|skull|rock|crystal|ice|chocolate|strawberry|apple|sunflower|card|basket|pen|pencil|brush|chain|cross|crescent|halo|scythe|polearm|sheath|scabbard|bandage|bandages|towel|curtains|motor_vehicle|aircraft|watercraft|bicycle|motorcycle|car|bus|train|ship|boat|airplane|helicopter|spaceship|mecha|robot|drone|tank|submarine|watch|clock|wristwatch|handbag|purse|wallet|backpack|suitcase|luggage|baggage|satchel|briefcase|attache_case|tool|machine|machinery|device|gadget|appliance|equipment|instrument|apparatus|contraption|implement|utensil|tool|weapon|armament|ordnance|munition|explosive|bomb|grenade|missile|rocket|torpedo|mine)$/) { print line >> outdir "/objects.csv"; counts["objects"]++; hit=1 }

    # Scenes by last-word
    else if(lw ~ /^(room|building|house|home|apartment|mansion|castle|palace|fortress|tower|dungeon|cave|tunnel|bridge|road|street|highway|path|trail|alley|sidewalk|pier|dock|port|harbor|marina|beach|shore|coast|island|mountain|hill|valley|canyon|cliff|volcano|crater|forest|wood|woods|jungle|swamp|marsh|desert|plain|meadow|field|farm|garden|park|playground|stadium|arena|coliseum|amphitheater|theater|cinema|museum|library|school|university|college|academy|hospital|clinic|office|factory|warehouse|shop|store|market|restaurant|cafe|bar|pub|tavern|inn|hotel|motel|spa|onsen|bath|bathhouse|shower|pool|lake|river|ocean|sea|waterfall|fountain|well|sky|space|moon|sun|planet|star|galaxy|nebula|universe|dimension|realm|world|city|town|village|countryside|landscape|scenery|nature|environment|background|backdrop|setting|location|christmas|halloween|new_year|valentine|birthday|festival|celebration|party|ceremony|wedding|funeral)$/) { print line >> outdir "/scenes.csv"; counts["scenes"]++; hit=1 }

    # Composition by last-word
    else if(lw ~ /^(view|shot|angle|perspective|framing|composition|crop|closeup|close-up|bokeh|blur|vignette|border|frame|panorama|landscape|portrait|format)$/) { print line >> outdir "/composition.csv"; counts["composition"]++; hit=1 }

    # Lighting by last-word
    else if(lw ~ /^(light|lighting|rays|beam|beams|shine|glow|sparkle|twinkle|flare|shimmer|shadow|shade|silhouette|god_rays|sunlight|moonlight|candlelight|firelight|rain|snow|fog|mist|haze|storm|wind|breeze|lightning|thunder|rainbow|aurora|sunset|sunrise|dawn|dusk|twilight|night|day|evening|morning|noon|midnight|steam|smoke|fire|flame|embers|ash)$/) { print line >> outdir "/lighting.csv"; counts["lighting"]++; hit=1 }

    # Style by last-word
    else if(lw ~ /^(art|style|drawing|painting|illustration|sketch|lineart|medium|media|technique|shading|color|colored|tone|monochrome|greyscale|grayscale|silhouette|outline|background|censored|censoring|censor|mosaic|resolution|quality|filter|effect|4koma|2koma|meme|parody|fanart|doujinshi|cosplay|oekaki)$/) { print line >> outdir "/style.csv"; counts["style"]++; hit=1 }

    # Actions by last-word
    else if(lw ~ /^(walking|running|jumping|dancing|flying|swimming|climbing|crawling|hopping|skipping|fighting|punching|kicking|grabbing|pulling|pushing|throwing|swinging|slashing|blocking|hugging|kissing|touching|caressing|stroking|petting|patting|tickling|sleeping|resting|waiting|hiding|peeking|pointing|waving|saluting|bowing|praying|begging|pleading|lifting|throwing|threw|caught|dropping|opening|closing|pouring|sweeping|washing|cleaning|cooking|baking|singing|speaking|shouting|whispering|yelling|screaming|laughing|giggling|eating|drinking|reading|writing|drawing|painting|smoking|wielding|straddling|mounting|dismounting|boarding|floating|wading|undressing)$/) { print line >> outdir "/actions.csv"; counts["actions"]++; hit=1 }

    # Sex acts by last-word
    else if(lw ~ /^(sex|anal|vaginal|fellatio|cunnilingus|deepthroat|facesitting|paizuri|footjob|handjob|masturbation|fingering|missionary|cowgirl|doggystyle|spooning|threesome|gangbang|orgy|harem|ahegao|cum|ejaculation|creampie|bukkake|facial|bondage|bdsm|restrained|gagged|blindfold|shibari|bound|rape|molestation|groping|forced|dildo|vibrator|condom|butt_plug|penetration|exhibitionism|voyeurism|peeping|upskirt|pantyshot|incest|bestiality|necrophilia|oral|erection|naked|nude|topless|bottomless|undressing|stripping|stripped|disrobing)$/) { print line >> outdir "/sex_acts.csv"; counts["sex_acts"]++; hit=1 }

    # Text features by last-word
    else if(lw ~ /^(text|bubble|bubbles|signature|watermark|username|name|logo|brand|dialogue|monologue|screen|ui|interface|message|notification|menu|bar|popup|window|dialog|alert|overlay|hud|display)$/) { print line >> outdir "/text_features.csv"; counts["text_features"]++; hit=1 }

    # Subjects by last-word
    else if(lw ~ /^(girls|boys|girl|boy|female|male|woman|man|lady|lord|child|children|baby|infant|toddler|teen|teenager|adult|elder|senior|couple|pair|duo|trio|group|team|party|squad|crew|gang|crowd|audience)$/) { print line >> outdir "/subjects.csv"; counts["subjects"]++; hit=1 }

    # Audio features
    else if(lw ~ /^(sfx|onomatopoeia|sound|audio|music|note|notes|lyrics|song|voice|noise)$/) { print line >> outdir "/audio_features.csv"; counts["audio_features"]++; hit=1 }
  }

  # --- fallback: other ---
  if(!hit) { print line >> outdir "/other.csv"; counts["other"]++ }
  else { matched_tags++ }

  if(total % 1000 == 0) printf "Processing... %d / 24317\r", total > "/dev/stderr"
}

END {
  printf "Processing... %d / 24317 (done)\n", total > "/dev/stderr"
  print "" > "/dev/stderr"
  print "=== Categorization Report ==="
  print ""
  printf "%-25s %s\n", "Category", "Count"
  print "----------------------------------------"
  n=split("subjects,body_parts,clothing,poses,expressions,composition,lighting,scenes,objects,style,actions,sex_acts,body_traits,text_features,audio_features,other", order, ",")
  sum=0
  for(i=1;i<=n;i++) { c=order[i]; v=counts[c]; sum+=v; printf "%-25s %d\n", c, v }
  print "----------------------------------------"
  printf "%-25s %d\n", "TOTAL (with overlaps)", sum
  printf "%-25s %d\n", "Unique tags", total
  printf "%-25s %d (%.1f%%)\n", "Matched tags", matched_tags, (matched_tags/total)*100
  printf "%-25s %d (%.1f%%)\n", "Other (unmatched)", counts["other"], (counts["other"]/total)*100
}
' "$INPUT"

echo ""
echo "=== Output files ==="
for cat in subjects body_parts clothing poses expressions composition \
            lighting scenes objects style actions sex_acts body_traits \
            text_features audio_features other; do
  count=$(wc -l < "$OUTPUT_DIR/${cat}.csv")
  printf "  %-20s %d lines\n" "${cat}.csv" "$count"
done
echo ""
echo "Done! Output written to: $OUTPUT_DIR"
