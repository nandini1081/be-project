INSERT INTO questions
(question_id, question_text, category, difficulty, topics, job_roles, embedding, ideal_keywords, created_at, updated_at)
VALUES

-- ===== THREAD 1: MODEL PERFORMANCE =====
('Q001','Your ML model performs well on training data but poorly on validation data. What is your first suspicion and why?','technical','easy','["ML"]','["Software Engineer"]','[]','["overfitting","generalization","training-validation gap"]','2026-01-22','2026-01-22'),

('Q002','How would you confirm whether overfitting is actually the root cause?','technical','medium','["ML"]','["Software Engineer"]','[]','["learning curves","cross validation","regularization"]','2026-01-22','2026-01-22'),

('Q003','If regularization lowers training accuracy but improves validation stability, would you deploy the model?','situational','medium','["ML"]','["Software Engineer"]','[]','["bias variance tradeoff","stability","business impact"]','2026-01-22','2026-01-22'),

('Q004','How does your debugging strategy change if this model is already in production?','technical','hard','["AI","ML"]','["Software Engineer"]','[]','["data drift","monitoring","rollback"]','2026-01-22','2026-01-22'),

('Q005','Describe a situation where you had to explain a model failure to a non-technical stakeholder.','behavioral','hard','["ML"]','["Software Engineer"]','[]','["communication","accountability","simplification"]','2026-01-22','2026-01-22'),

-- ===== THREAD 2: DATA QUALITY =====
('Q006','What data quality checks do you perform before starting any analysis?','technical','easy','["Data Analyst"]','["Software Engineer"]','[]','["missing values","duplicates","outliers"]','2026-01-22','2026-01-22'),

('Q007','How do you decide whether an outlier should be removed or kept?','technical','medium','["Data Analyst"]','["Software Engineer"]','[]','["domain knowledge","distribution","impact analysis"]','2026-01-22','2026-01-22'),

('Q008','If business teams want to keep noisy data, how do you handle the disagreement?','situational','medium','["Data Analyst"]','["Software Engineer"]','[]','["evidence","visualization","stakeholder communication"]','2026-01-22','2026-01-22'),

('Q009','How would you quantify the impact of poor data quality on model performance?','technical','hard','["ML","Data Analyst"]','["Software Engineer"]','[]','["ablation study","error analysis","sensitivity"]','2026-01-22','2026-01-22'),

('Q010','Tell me about a project where data quality issues forced you to redesign your solution.','behavioral','hard','["Data Analyst"]','["Software Engineer"]','[]','["adaptability","problem solving","decision making"]','2026-01-22','2026-01-22'),

-- ===== THREAD 3: FEATURE ENGINEERING =====
('Q011','What characteristics make a feature useful for a machine learning model?','technical','easy','["ML"]','["Software Engineer"]','[]','["predictive signal","relevance","variance"]','2026-01-22','2026-01-22'),

('Q012','How do you verify that a new feature genuinely improves a model?','technical','medium','["ML"]','["Software Engineer"]','[]','["ablation","cross validation","metric comparison"]','2026-01-22','2026-01-22'),

('Q013','A feature improves offline metrics but hurts real-world performance. What could be the reason?','situational','medium','["ML"]','["Software Engineer"]','[]','["data leakage","distribution shift","proxy feature"]','2026-01-22','2026-01-22'),

('Q014','Explain feature leakage using a real-world example.','technical','hard','["ML"]','["Software Engineer"]','[]','["target leakage","temporal leakage","causality"]','2026-01-22','2026-01-22'),

('Q015','Describe a feature you removed after initially believing it was important.','behavioral','hard','["ML"]','["Software Engineer"]','[]','["learning","iteration","evidence driven"]','2026-01-22','2026-01-22'),

-- ===== THREAD 4: MODEL SELECTION =====
('Q016','When would you choose logistic regression over more complex models?','technical','easy','["ML"]','["Software Engineer"]','[]','["interpretability","baseline","simplicity"]','2026-01-22','2026-01-22'),

('Q017','How do you choose between two models with similar performance metrics?','technical','medium','["ML"]','["Software Engineer"]','[]','["latency","maintainability","explainability"]','2026-01-22','2026-01-22'),

('Q018','Leadership wants a deep learning model, but simpler models perform better. What do you do?','situational','medium','["AI","ML"]','["Software Engineer"]','[]','["trade-offs","business alignment","evidence"]','2026-01-22','2026-01-22'),

('Q019','How do you fairly compare models trained on different feature sets?','technical','hard','["ML"]','["Software Engineer"]','[]','["controlled experiments","fair evaluation"]','2026-01-22','2026-01-22'),

('Q020','Tell me about a time you pushed back against unnecessary technical complexity.','behavioral','hard','["AI"]','["Software Engineer"]','[]','["judgment","communication","impact"]','2026-01-22','2026-01-22'),

-- ===== THREAD 5: DEPLOYMENT & MONITORING =====
('Q021','What challenges arise when moving an ML model from experimentation to production?','technical','easy','["ML"]','["Software Engineer"]','[]','["reproducibility","versioning","latency"]','2026-01-22','2026-01-22'),

('Q022','What metrics would you continuously monitor for a deployed ML model?','technical','medium','["AI","ML"]','["Software Engineer"]','[]','["drift","performance","alerts"]','2026-01-22','2026-01-22'),

('Q023','Inference latency spikes during peak traffic. How would you investigate?','situational','medium','["AI"]','["Software Engineer"]','[]','["profiling","bottleneck","scaling"]','2026-01-22','2026-01-22'),

('Q024','Design a scalable inference architecture for millions of users.','technical','hard','["AI","ML"]','["Software Engineer"]','[]','["load balancing","horizontal scaling","caching"]','2026-01-22','2026-01-22'),

('Q025','Describe a production issue you detected before users noticed it.','behavioral','hard','["AI"]','["Software Engineer"]','[]','["ownership","monitoring","proactiveness"]','2026-01-22','2026-01-22'),

-- ===== THREAD 6: ETHICS, ANALYTICS, DECISION MAKING =====
('Q026','What does bias mean in the context of machine learning models?','technical','easy','["AI","ML"]','["Software Engineer"]','[]','["bias","fairness","representation"]','2026-01-22','2026-01-22'),

('Q027','How can biased data negatively impact real-world decisions?','situational','medium','["AI"]','["Software Engineer"]','[]','["ethical impact","skewed outcomes"]','2026-01-22','2026-01-22'),

('Q028','How would you detect bias in a deployed AI system?','technical','hard','["AI","ML"]','["Software Engineer"]','[]','["fairness metrics","monitoring","subgroup analysis"]','2026-01-22','2026-01-22'),

('Q029','Tell me about an ethical concern you encountered while working with data or AI.','behavioral','hard','["AI"]','["Software Engineer"]','[]','["ethics","responsibility","decision making"]','2026-01-22','2026-01-22'),

('Q030','How do you balance business intuition with data-driven insights?','behavioral','hard','["Data Analyst"]','["Software Engineer"]','[]','["judgment","trade-offs","decision making"]','2026-01-22','2026-01-22'),

('Q031','What is A/B testing and when would you use it?','technical','easy','["Data Analyst"]','["Software Engineer"]','[]','["A/B testing","experimentation","control group"]','2026-01-22','2026-01-22'),

('Q032','How do you design an experiment to ensure statistically valid results?','technical','medium','["Data Analyst"]','["Software Engineer"]','[]','["randomization","sample size","statistical power"]','2026-01-22','2026-01-22'),

('Q033','If an experiment shows inconclusive results, how do you proceed?','situational','medium','["Data Analyst"]','["Software Engineer"]','[]','["confidence intervals","iteration","decision making"]','2026-01-22','2026-01-22'),

('Q034','Explain a time-series forecasting approach you have used.','technical','hard','["ML","Data Analyst"]','["Software Engineer"]','[]','["trend","seasonality","forecasting"]','2026-01-22','2026-01-22'),

('Q035','Describe a time your data-driven recommendation was challenged or rejected.','behavioral','hard','["Data Analyst"]','["Software Engineer"]','[]','["resilience","feedback","learning"]','2026-01-22','2026-01-22'),

('Q036','How do you validate insights before presenting them to leadership?','technical','medium','["Data Analyst"]','["Software Engineer"]','[]','["sanity checks","cross validation","confidence"]','2026-01-22','2026-01-22'),

('Q037','If leadership questions your analysis, how do you defend it?','situational','medium','["Data Analyst"]','["Software Engineer"]','[]','["data backed reasoning","communication"]','2026-01-22','2026-01-22'),

('Q038','Explain a recommendation system you have designed or studied.','technical','hard','["AI","ML"]','["Software Engineer"]','[]','["collaborative filtering","ranking","evaluation"]','2026-01-22','2026-01-22'),

('Q039','How do you ensure data privacy when building ML systems?','technical','hard','["AI","Data Analyst"]','["Software Engineer"]','[]','["anonymization","access control","compliance"]','2026-01-22','2026-01-22'),

('Q040','Tell me about a time you had to learn a new data or ML concept quickly.','behavioral','medium','["ML","Data Analyst"]','["Software Engineer"]','[]','["learning","adaptability","initiative"]','2026-01-22','2026-01-22'),

('Q041','What trade-offs do you consider when choosing real-time versus batch processing?','technical','medium','["Data Analyst","AI"]','["Software Engineer"]','[]','["latency","consistency","cost"]','2026-01-22','2026-01-22'),

('Q042','Describe a scenario where simpler analytics outperformed complex modeling.','situational','medium','["Data Analyst"]','["Software Engineer"]','[]','["simplicity","interpretability","impact"]','2026-01-22','2026-01-22'),

('Q043','How do you debug silent failures in data pipelines?','technical','hard','["Data Analyst","AI"]','["Software Engineer"]','[]','["logging","data validation","monitoring"]','2026-01-22','2026-01-22'),

('Q044','Tell me about a time you improved a pipeline or model for efficiency rather than accuracy.','behavioral','medium','["AI","ML"]','["Software Engineer"]','[]','["optimization","trade-offs","impact"]','2026-01-22','2026-01-22'),

('Q045','How do you mentor junior team members on data or ML concepts?','behavioral','medium','["AI","ML"]','["Software Engineer"]','[]','["mentorship","knowledge sharing"]','2026-01-22','2026-01-22'),

('Q046','What risks do you consider before deploying an AI system affecting users directly?','technical','hard','["AI"]','["Software Engineer"]','[]','["risk assessment","ethics","monitoring"]','2026-01-22','2026-01-22'),

('Q047','Describe a situation where monitoring revealed an unexpected issue.','behavioral','medium','["AI"]','["Software Engineer"]','[]','["observability","problem solving"]','2026-01-22','2026-01-22'),

('Q048','How would you explain model confidence to a product manager?','situational','easy','["ML"]','["Software Engineer"]','[]','["probability","uncertainty","interpretation"]','2026-01-22','2026-01-22'),

('Q049','What makes an ML system maintainable over time?','technical','medium','["AI","ML"]','["Software Engineer"]','[]','["documentation","versioning","monitoring"]','2026-01-22','2026-01-22'),

('Q050','Tell me about a project where data influenced a major engineering decision.','behavioral','hard','["Data Analyst","AI"]','["Software Engineer"]','[]','["impact","decision making","evidence"]','2026-01-22','2026-01-22');
