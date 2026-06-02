// ============================================
// 汉献帝之末路 v2.5.0 — 拟旨面板 EdictComposer
// 9 维旨意表单 (v2.2.0 借鉴明末) + 标签页分组
// 字段: target/executor/scope/resources/deadline/authority/incentive/constraints/publicity
// ============================================

import React, { useState } from 'react';
import { AuthoritySlider, AuthorityLevel } from './AuthoritySlider';
import './EdictComposer.css';

export interface Directive {
  id?: string;
  kind?: string;
  target: string;          // 对象
  executor: string;        // 执行人
  scope: string;           // 范围
  resources: string;       // 资源
  deadline: string;        // 期限
  authority: AuthorityLevel;  // 5 档权限
  incentive: string;       // 激励
  constraints: string;     // 约束
  publicity: string;       // 公示
}

export interface EdictComposerProps {
  initial?: Partial<Directive>;
  onSubmit?: (d: Directive) => void;
  onCancel?: () => void;
  onPreview?: (d: Directive) => void;
}

const TAB_GROUPS = [
  { key: 'basic', label: '基础', fields: ['target', 'executor', 'scope'] },
  { key: 'resource', label: '资源', fields: ['resources', 'deadline'] },
  { key: 'authority', label: '权限', fields: ['authority'] },
  { key: 'detail', label: '细则', fields: ['incentive', 'constraints', 'publicity'] },
] as const;

const KIND_PRESETS = [
  '颁布新政', '兴修水利', '减免赋税', '调兵遣将', '任免官员', '赈济灾荒',
];

export const EdictComposer: React.FC<EdictComposerProps> = ({
  initial,
  onSubmit,
  onCancel,
  onPreview,
}) => {
  const [activeTab, setActiveTab] = useState<typeof TAB_GROUPS[number]['key']>('basic');
  const [directive, setDirective] = useState<Directive>({
    target: initial?.target || '',
    executor: initial?.executor || '',
    scope: initial?.scope || '全国',
    resources: initial?.resources || '',
    deadline: initial?.deadline || '本月',
    authority: initial?.authority || 3,
    incentive: initial?.incentive || '',
    constraints: initial?.constraints || '',
    publicity: initial?.publicity || '邸报',
    kind: initial?.kind || '颁布新政',
  });

  const update = <K extends keyof Directive>(key: K, value: Directive[K]) => {
    setDirective((d) => ({ ...d, [key]: value }));
  };

  const handleSubmit = () => {
    if (!directive.target.trim()) {
      alert('请填写旨意对象');
      return;
    }
    onSubmit?.(directive);
  };

  return (
    <div className="edict-composer">
      <div className="edict-composer-header">
        <h3 className="edict-composer-title imperial">拟旨</h3>
        <div className="edict-composer-presets">
          {KIND_PRESETS.map((k) => (
            <button type="button"
              key={k}
              className={`edict-composer-preset ${directive.kind === k ? 'edict-composer-preset-active' : ''}`}
              onClick={() => update('kind', k)}
            >
              {k}
            </button>
          ))}
        </div>
      </div>

      <div className="edict-composer-tabs">
        {TAB_GROUPS.map((t) => (
          <button type="button"
            key={t.key}
            className={`edict-composer-tab ${activeTab === t.key ? 'edict-composer-tab-active' : ''}`}
            onClick={() => setActiveTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="edict-composer-body">
        {activeTab === 'basic' && (
          <div className="edict-composer-form">
            <Field label="旨意对象" required>
              <input
                className="edict-composer-input"
                value={directive.target}
                onChange={(e) => update('target', e.target.value)}
                placeholder="如: 冀州百姓 / 兖州牧曹操 / 司隶校尉"
              />
            </Field>
            <Field label="执行人">
              <input
                className="edict-composer-input"
                value={directive.executor}
                onChange={(e) => update('executor', e.target.value)}
                placeholder="如: 曹操 / 张辽 / 地方官"
              />
            </Field>
            <Field label="施行范围">
              <input
                className="edict-composer-input"
                value={directive.scope}
                onChange={(e) => update('scope', e.target.value)}
                placeholder="全国 / 冀州 / 军中"
              />
            </Field>
          </div>
        )}

        {activeTab === 'resource' && (
          <div className="edict-composer-form">
            <Field label="所需资源">
              <textarea
                className="edict-composer-textarea"
                value={directive.resources}
                onChange={(e) => update('resources', e.target.value)}
                placeholder="如: 钱十万缗 / 粮三千斛 / 兵五千"
                rows={3}
              />
            </Field>
            <Field label="期限">
              <input
                className="edict-composer-input"
                value={directive.deadline}
                onChange={(e) => update('deadline', e.target.value)}
                placeholder="本月 / 季内 / 年内"
              />
            </Field>
          </div>
        )}

        {activeTab === 'authority' && (
          <div className="edict-composer-form">
            <Field label="旨意权限" hint="5 档: 口谕(弱) → 廷议(强)">
              <AuthoritySlider
                value={directive.authority}
                onChange={(v) => update('authority', v)}
              />
            </Field>
            <div className="edict-composer-authority-hint">
              当前: <strong className="imperial">
                {['', '口谕', '谕旨', '圣旨', '密旨', '廷议'][directive.authority]}
              </strong>
              <span className="edict-composer-authority-desc">
                ({['', '当面口述, 轻诺', '颁行州郡, 中度', '昭告天下, 高度', '暗授亲信, 高度隐秘', '朝会议定, 最高权威'][directive.authority]})
              </span>
            </div>
          </div>
        )}

        {activeTab === 'detail' && (
          <div className="edict-composer-form">
            <Field label="激励">
              <input
                className="edict-composer-input"
                value={directive.incentive}
                onChange={(e) => update('incentive', e.target.value)}
                placeholder="赏金 / 赐爵 / 加官"
              />
            </Field>
            <Field label="约束">
              <textarea
                className="edict-composer-textarea"
                value={directive.constraints}
                onChange={(e) => update('constraints', e.target.value)}
                placeholder="如: 不得扰民 / 不得擅杀"
                rows={2}
              />
            </Field>
            <Field label="公示">
              <input
                className="edict-composer-input"
                value={directive.publicity}
                onChange={(e) => update('publicity', e.target.value)}
                placeholder="邸报 / 州郡榜 / 暗授"
              />
            </Field>
          </div>
        )}
      </div>

      <div className="edict-composer-footer">
        <button type="button" className="edict-composer-btn edict-composer-btn-cancel" onClick={onCancel}>
          取消
        </button>
        <button type="button" className="edict-composer-btn edict-composer-btn-preview" onClick={() => onPreview?.(directive)}>
          预览
        </button>
        <button type="button" className="edict-composer-btn edict-composer-btn-submit" onClick={handleSubmit}>
          颁旨
        </button>
      </div>
    </div>
  );
};

// === Field 子组件 ===
const Field: React.FC<{ label: string; required?: boolean; hint?: string; children: React.ReactNode }> = ({
  label, required, hint, children,
}) => (
  <div className="edict-composer-field">
    <label className="edict-composer-label">
      {label}
      {required && <span className="edict-composer-required">*</span>}
      {hint && <span className="edict-composer-hint">{hint}</span>}
    </label>
    {children}
  </div>
);

export default EdictComposer;
