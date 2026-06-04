# Danbooru 标签系统完整参考手册

> 来源：Danbooru Wiki、Moescape、CivitAI、各类 SD 模型文档
> 整理日期：2026-06-04

---

## 一、五大标签类别

| 类别 | ID | 颜色 | 用途 | 示例 |
|------|----|------|------|------|
| General | 0 | 蓝色 | 视觉描述性标签 | `1girl`, `sitting`, `blue_hair` |
| Artist | 1 | 红色 | 创作者标识 | `wlop`, `kantoku` |
| Copyright | 3 | 紫色 | 来源系列 | `genshin_impact`, `original` |
| Character | 4 | 绿色 | 角色标识 | `hakurei_reimu` |
| Meta | 5 | 黄色 | 系统/元数据 | `highres`, `absurdres` |

---

## 二、提示词结构模板（SDXL / Illustrious 模型）

```
1. 主体与数量     → 1girl, 1boy, 2girls, solo
2. 角色与系列     → yae_miko, genshin_impact
3. 外貌特征       → hair color, eye color, body type
4. 表情           → smile, blush, wide_eyed
5. 姿势/动作      → standing, sitting, looking_at_viewer
6. 服装           → dress, thighhighs, hat
7. 背景/场景      → beach, sunset, indoors
8. 构图/景别      → portrait, upper_body, full_body
9. 光线/氛围      → sunlight, cinematic_lighting, soft_light
10. 风格标签      → illustration, sketch, photorealistic
11. 质量关键词     → masterpiece, best quality, absurdres (放开头或末尾)
```

---

## 三、权重语法速查

| 语法 | 含义 | 默认倍率 |
|------|------|---------|
| `(tag)` | 增加权重 | ×1.1 |
| `((tag))` | 双重增加 | ×1.21 |
| `(((tag)))` | 三重增加 | ×1.33 |
| `[tag]` | 降低权重 | ×0.9 |
| `[[tag]]` | 双重降低 | ×0.81 |
| `(tag:1.3)` | 精确权重 | 推荐 0.5~2.0 |
| `<lora:name:0.8>` | LoRA 引用 | Impact Pack 原生支持 |
| `BREAK` | 分割条件化 | 需 ImpactWildcardEncode 节点 |

**注意事项：**
- 精确权重 `(tag:weight)` 优于堆叠括号（更精确可读）
- 权重超 2.0 产生伪影，低于 0.5 几乎移除概念
- 前 75 个 token 最重要——关键概念放前面
- 英文逗号 `,` 分隔，不可用中文逗号 `，`

---

## 四、核心姿势标签（Tag Group: Posture）

### 站立
| 标签 | 含义 |
|------|------|
| `standing` | 直立 |
| `contrapposto` | 重心在单腿，臀部偏移 |
| `wide_stance` | 双腿分开站立 |
| `on_one_leg` | 单腿站立 |

### 坐姿
| 标签 | 含义 |
|------|------|
| `sitting` | 一般坐姿 |
| `seiza` | 正坐（跪坐） |
| `indian_style` | 盘腿坐 |
| `wariza` | 腿向两侧弯曲（W坐姿） |
| `yokozuwari` | 腿向一侧 |
| `crossed_legs` | 翘腿 |
| `legs_folded` | 腿向身体收起 |
| `lotus_position` | 莲花坐 |
| `knees_together_feet_apart` | 膝并拢脚分开 |

### 跪姿与蹲姿
| 标签 | 含义 |
|------|------|
| `kneeling` | 双膝跪地 |
| `on_one_knee` | 单膝跪地 |
| `squatting` | 蹲姿（双脚着地） |
| `crouching` | 俯身蹲姿 |

### 卧姿与倚靠
| 标签 | 含义 |
|------|------|
| `lying` | 躺 |
| `reclining` | 半躺倚靠 |
| `on_stomach` | 俯卧 |
| `on_back` | 仰卧 |
| `on_side` | 侧卧 |
| `fetal_position` | 蜷缩（胎儿姿势） |
| `hugging_own_legs` | 抱膝 |

### 动态姿势
| 标签 | 含义 |
|------|------|
| `dynamic_pose` | 一般动态姿势 |
| `fighting_stance` | 格斗架势 |
| `all_fours` | 四肢着地 |
| `bent_over` | 弯腰 |
| `stretching` | 伸展 |
| `reaching` | 伸手 |
| `leaning_forward` | 前倾 |
| `leaning_back` | 后靠 |
| `leg_up` | 单腿抬起 |
| `leg_split` | 劈叉 |
| `handstand` | 倒立 |

---

## 五、手臂与手势标签（Tag Group: Gestures）

### 手臂
| 标签 | 含义 |
|------|------|
| `crossed_arms` | 双臂交叉 |
| `arms_behind_back` | 双手背后 |
| `arms_up` | 双手举过头 |
| `arm_rest` | 手臂搁在表面 |
| `arm_support` | 手臂支撑身体 |
| `outstretched_arm` | 手臂伸展 |
| `hand_on_hip` | 叉腰 |
| `hand_in_pocket` | 手插口袋 |
| `hand_on_own_cheek` | 手托腮 |
| `hands_on_own_knees` | 手放膝上 |
| `hands_behind_head` | 双手抱头 |

### 单手手势
| 标签 | 含义 |
|------|------|
| `pointing_at_viewer` | 指向观众 |
| `pointing_up` / `pointing_down` | 指向上下 |
| `thumbs_up` / `thumbs_down` | 拇指上下 |
| `middle_finger` | 竖中指 |
| `index_finger_raised` | 食指竖起 |
| `peace_sign` / `v_sign` | V字手势 |
| `finger_gun` | 手指枪 |
| `crossed_fingers` | 交叉手指 |
| `finger_heart` | 手指比心 |
| `shaka_sign` | 夏威夷手势 |
| `salute` | 敬礼 |

### 双手手势
| 标签 | 含义 |
|------|------|
| `heart_hands` | 双手比心 |
| `clenched_hands` | 握紧双手 |
| `open_hands` | 张开双手 |
| `prayer` | 双手合十 |
| `high_five` | 击掌 |
| `steepled_fingers` | 指尖相对 |
| `x_arms` | 双臂交叉成 X 形 |
| `holding_hands` | 牵手 |
| `handshake` | 握手 |

---

## 六、表情标签

| 标签 | 含义 | 备注 |
|------|------|------|
| `smile` | 微笑 | |
| `grin` | 咧嘴笑 | 露齿 |
| `frown` | 皱眉 | |
| `smirk` | 得意笑 | |
| `blush` | 脸红 | |
| `angry` | 愤怒 | |
| `surprised` | 惊讶 | |
| `sad` | 悲伤 | |
| `crying` | 哭泣 | 暗示 `streaming_tears` |
| `happy_tears` | 喜极而泣 | |
| `despair` | 绝望 | |
| `gloom_(expression)` | 喜剧性抑郁 | |
| `sweatdrop` | 汗滴 | |
| `anger_vein` | 愤怒青筋 | |
| `nosebleed` | 鼻血 | |

### 眼睛状态
| 标签 | 含义 |
|------|------|
| `open_eyes` | 睁眼 |
| `closed_eyes` | 闭眼 |
| `half-closed_eyes` | 半闭眼（困倦/诱惑） |
| `wide_eyed` | 睁大眼（惊讶） |
| `one_eye_closed` | 单眼闭（眨眼） |
| `heart_eyes` | 心形眼 |
| `star_eyes` | 星形眼 |
| `dilated_pupils` | 瞳孔放大 |

### 嘴部
| 标签 | 含义 |
|------|------|
| `open_mouth` | 张嘴 |
| `closed_mouth` | 闭嘴 |
| `parted_lips` | 微张（介于开闭之间） |
| `teeth` | 牙齿可见 |
| `tongue_out` | 吐舌 |
| `biting_lip` | 咬唇 |
| `licking_lips` | 舔唇 |

---

## 七、视线与目光方向

| 标签 | 含义 |
|------|------|
| `looking_at_viewer` | 看向观众 |
| `looking_away` | 移开视线（已弃用） |
| `averting_eyes` | 故意移开视线 |
| `looking_to_the_side` | 看向侧面 |
| `looking_ahead` | 看向前方 |
| `looking_afar` | 看向远方 |
| `looking_down` | 角色向下看 |
| `looking_up` | 角色向上看 |
| `looking_back` | 回头看向观众 |
| `facing_viewer` | 面向观众 |
| `facing_away` | 脸转离观众 |
| `eye_contact` | 眼神接触 |

---

## 八、相机角度与构图（Tag Group: Image Composition）

| 标签 | 含义 |
|------|------|
| `from_above` | 相机从上方俯拍 |
| `from_below` | 相机从下方仰拍 |
| `aerial_view` | 鸟瞰 |
| `dutch_angle` | 倾斜角度 |
| `fisheye` | 鱼眼超广角 |
| `front_view` | 正面视角 |
| `side_view` | 侧面视角 |
| `back_view` / `rear_view` | 背面视角 |
| `turned_back` | 角色背对观众 |
| `full_body` | 全身 |
| `cowboy_shot` | 大腿处裁剪（~60-70%身体） |
| `cropped_legs` | 腿部出画 |
| `close-up` | 面部特写 |
| `upper_body` | 上半身（腰部以上） |
| `selfie` | 自拍构图 |
| `multiple_views` | 多角度展示 |
| `pov` | 第一人称视角 |
| `foreshortening` | 透视缩短 |
| `wide_shot` | 广角远景 |
| `depth_of_field` | 景深 |

---

## 九、光线与氛围

| 标签 | 含义 |
|------|------|
| `sunlight` | 阳光 |
| `backlighting` | 逆光 |
| `sunbeam` | 丁达尔光束 |
| `moonlight` | 月光 |
| `chiaroscuro` | 明暗对照（戏剧性光影） |
| `silhouette` | 剪影 |
| `cinematic_lighting` | 电影级布光 |
| `soft_light` | 柔光 |
| `harsh_light` | 硬光 |
| `lens_flare` | 镜头光晕 |
| `fog` | 雾 |
| `rain` | 雨 |
| `snow` | 雪 |
| `sparkle` | 闪光/星星点 |
| `glowing` | 发光 |
| `neon_lights` | 霓虹灯 |

---

## 十、质量标签系统

### Illustrious / NoobAI 系列
```
masterpiece, best quality, amazing quality, newest, absurdres
```
| 百分位 | 标签 |
|--------|------|
| > 95% | `masterpiece` |
| > 85% | `best quality` |
| > 60% | `good quality` |
| > 30% | `normal quality` |
| <= 30% | `worst quality` |

### Pony Diffusion（不可混用！）
```
score_9, score_8_up, score_7_up, score_6_up
```

### 通用负面提示词
```
worst quality, bad quality, low quality, lowres, bad anatomy, bad hands,
watermark, signature, blurry, ugly, deformed, extra limbs, poorly drawn face,
jpeg artifacts
```

---

## 十一、Impact Pack 通配符语法

| 语法 | 效果 |
|------|------|
| `{a\|b\|c}` | 随机选一项 |
| `__filename__` | 从该文件随机选一行 |
| `{2-4$$\|opt1\|opt2}` | 选2-4项，`$$`分隔 |
| `5#__wildcard__` | 重复通配符5次 |
| `{5::weight_a\|4::weight_b\|c}` | 加权随机（v4.15.1+） |
| `BREAK` | 分割条件化 |
| `<lora:name:weight>` | 加载LoRA |
| `<lora:name:weight:clip_weight>` | 带CLIP权重的LoRA |
| `# 注释` | 注释行（运行时移除） |

---

## 十二、常见错误避免

1. **不混用质量系统**：Pony `score_9` ≠ Danbooru `masterpiece`
2. **不用中文逗号**：`,` 是分隔符，`，` 是 token 内容
3. **不过度加权**：从 1.2-1.4 开始，2.0 以上产生伪影
4. **不忽略 LoRA 触发词**：多数 LoRA 需要特定触发 token
5. **BREAK 需要自定义节点**：原生 CLIPTextEncode 不支持
6. **`looking_*` ≠ `from_*`**：`looking_down` = 角色向下看；`from_above` = 相机俯拍
