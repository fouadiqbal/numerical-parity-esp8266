#!/usr/bin/env python3
"""Build the curated Phase 23 related-work evidence and bibliography."""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "results"
TABLES = ROOT / "tables"
REFERENCES = ROOT / "references"


STUDIES = [
    {
        "key": "shi2018pooling",
        "authors": "Heng Shi and Minghao Xu and Ran Li",
        "authors_short": "Shi et al.",
        "year": 2018,
        "title": "Deep Learning for Household Load Forecasting—A Novel Pooling Deep RNN",
        "venue": "IEEE Transactions on Smart Grid",
        "volume": "9",
        "number": "5",
        "pages": "5271--5280",
        "doi": "10.1109/TSG.2017.2686012",
        "url": "https://doi.org/10.1109/TSG.2017.2686012",
        "problem": "Individual-household load forecasting under high volatility.",
        "dataset": "Irish smart-meter data from 920 customers.",
        "model": "Pooling-based deep recurrent neural network (PDRNN).",
        "hardware": "TensorFlow development platform; no constrained-device deployment reported.",
        "evaluation": "Forecasting RMSE compared with ARIMA, SVR, and a classical deep RNN.",
        "limitation": "Accuracy study rather than embedded portability or anomaly detection.",
        "difference": "Our model is far simpler and less broadly validated, but adds generated C++ export and complete physical ESP8266 numerical/decision parity.",
        "table11": True,
        "temporal_evaluation": "Study-specific train/test forecasting; no rolling-origin result used in our comparison",
        "anomaly_evidence": "None",
        "full_vector_parity": "Not reported",
        "measured_cost": "No MCU cost reported",
    },
    {
        "key": "kong2019lstm",
        "authors": "Weicong Kong and Zhao Yang Dong and Youwei Jia and David J. Hill and Yan Xu and Yuan Zhang",
        "authors_short": "Kong et al.",
        "year": 2019,
        "title": "Short-Term Residential Load Forecasting Based on LSTM Recurrent Neural Network",
        "venue": "IEEE Transactions on Smart Grid",
        "volume": "10",
        "number": "1",
        "pages": "841--851",
        "doi": "10.1109/TSG.2017.2753802",
        "url": "https://doi.org/10.1109/TSG.2017.2753802",
        "problem": "Short-term load forecasting for individual residential customers.",
        "dataset": "Public real residential smart-meter dataset.",
        "model": "LSTM recurrent neural network with forecasting benchmarks.",
        "hardware": "No constrained-microcontroller execution reported.",
        "evaluation": "Individual-residential forecasts compared with multiple benchmark algorithms.",
        "limitation": "Focuses forecasting accuracy rather than reproducible software-to-device transfer.",
        "difference": "Our work does not challenge its forecasting novelty; it emphasizes compact deployment and deterministic cross-platform validation.",
        "table11": True,
        "temporal_evaluation": "Study-specific residential forecasting experiment; no rolling-origin result used here",
        "anomaly_evidence": "None",
        "full_vector_parity": "Not reported",
        "measured_cost": "No MCU cost reported",
    },
    {
        "key": "liu2018scalable",
        "authors": "Xiufeng Liu and Per Sieverts Nielsen",
        "authors_short": "Liu and Nielsen",
        "year": 2018,
        "title": "Scalable Prediction-Based Online Anomaly Detection for Smart Meter Data",
        "venue": "Information Systems",
        "volume": "77",
        "number": "",
        "pages": "34--47",
        "doi": "10.1016/j.is.2018.05.007",
        "url": "https://doi.org/10.1016/j.is.2018.05.007",
        "problem": "Online detection of unusual smart-meter consumption patterns at scale.",
        "dataset": "A real-world dataset and a large synthetic dataset.",
        "model": "Prediction-based detector within a batch/speed lambda architecture.",
        "hardware": "Big-data system architecture; no microcontroller deployment.",
        "evaluation": "Detection comparison with three baselines plus scalability experiments.",
        "limitation": "System-level online scalability is not evidence of TinyML feasibility or numerical portability.",
        "difference": "Our detector is much smaller and not validated at big-data scale, but its threshold decisions are checked end-to-end on a physical MCU.",
        "table11": True,
        "temporal_evaluation": "Online/iterative streaming evaluation",
        "anomaly_evidence": "Real and synthetic pattern-anomaly evaluation",
        "full_vector_parity": "Not applicable",
        "measured_cost": "Scalability; no MCU RAM/latency",
    },
    {
        "key": "utomo2020multitiered",
        "authors": "Darmawan Utomo and Pao-Ann Hsiung",
        "authors_short": "Utomo and Hsiung",
        "year": 2020,
        "title": "A Multitiered Solution for Anomaly Detection in Edge Computing for Smart Meters",
        "venue": "Sensors",
        "volume": "20",
        "number": "18",
        "pages": "5159",
        "doi": "10.3390/s20185159",
        "url": "https://doi.org/10.3390/s20185159",
        "problem": "Multitier prediction of future anomalous energy-use periods near the edge.",
        "dataset": "One year of 30-min data from 200 US households; labels based on a statistical rule.",
        "model": "DNN, SVR, and KNN with clustering and label expansion.",
        "hardware": "Raspberry Pi edge execution.",
        "evaluation": "PR-AUC, model size, training time, and inference latency; best DNN latency reported as 1.25 ms.",
        "limitation": "Raspberry Pi is substantially less constrained than ESP8266, and anomaly labels are constructed statistically.",
        "difference": "This is direct prior art for edge smart-meter anomaly analytics; our narrower distinction is complete MCU numerical and decision parity, not a new anomaly algorithm.",
        "table11": True,
        "temporal_evaluation": "Sliding windows and daily look-ahead labels",
        "anomaly_evidence": "Mean + 3 SD statistical labels, expanded over look-ahead windows",
        "full_vector_parity": "Not reported",
        "measured_cost": "Raspberry Pi latency and model file size",
    },
    {
        "key": "hu2020edge",
        "authors": "Hailin Hu and Liangrui Tang",
        "authors_short": "Hu and Tang",
        "year": 2020,
        "title": "Edge Intelligence for Real-Time Data Analytics in an IoT-Based Smart Metering System",
        "venue": "IEEE Network",
        "volume": "34",
        "number": "5",
        "pages": "68--74",
        "doi": "10.1109/MNET.011.2000039",
        "url": "https://doi.org/10.1109/MNET.011.2000039",
        "problem": "Low-latency cloud-edge data analytics for IoT smart metering.",
        "dataset": "Numerical smart-meter system experiments.",
        "model": "DNN within offline and online cloud-edge collaboration schemes.",
        "hardware": "Edge-enabled architecture; a specific ESP-class MCU parity experiment is not reported.",
        "evaluation": "Numerical results for execution-time/adaptability claims.",
        "limitation": "Architecture-level evidence does not isolate deterministic microcontroller inference portability.",
        "difference": "Our scope is smaller but provides byte-level model state, whole-firmware resources, and held-out prediction/decision agreement on ESP8266.",
        "table11": True,
        "temporal_evaluation": "Offline/online cloud-edge numerical evaluation",
        "anomaly_evidence": "Not the primary evaluation",
        "full_vector_parity": "Not reported",
        "measured_cost": "Execution-time results; no ESP8266 accounting",
    },
    {
        "key": "gajendran2026ihems",
        "authors": "Gajendran P and Ranganayaki V and Deepa S. N.",
        "authors_short": "Gajendran et al.",
        "year": 2026,
        "title": "IoT-Based Home Energy Management Using Machine Learning and BiLSTM–GRU Forecasting",
        "venue": "AIP Advances",
        "volume": "16",
        "number": "7",
        "pages": "075012",
        "doi": "10.1063/5.0339511",
        "url": "https://doi.org/10.1063/5.0339511",
        "problem": "IoT residential monitoring and short-term forecasting across two load zones.",
        "dataset": "PZEM-004T measurements from two residential halls, sampled every 5 s and aggregated hourly.",
        "model": "Linear/tree ensembles plus BiLSTM and GRU forecasting.",
        "hardware": "ESP8266 sensing/Wi-Fi gateways; forecasting evaluated on i7 CPU and RTX 3060 GPU.",
        "evaluation": "Chronological 70/15/15 split, forecasting RMSE, PC inference time/memory, and ESP8266 communication latency.",
        "limitation": "The ESP8266 transports measurements but does not execute the forecasting models reported in the performance table.",
        "difference": "This is direct ESP8266 smart-meter prior art with real sensing. Our distinct contribution is local ESP8266 model/decision execution and row-wise parity; their study is stronger on physical data acquisition.",
        "table11": True,
        "temporal_evaluation": "Chronological 70/15/15; next-hour prediction",
        "anomaly_evidence": "None",
        "full_vector_parity": "Not reported",
        "measured_cost": "PC ML latency/memory; ESP8266 link latency 72–95 ms",
    },
    {
        "key": "banbury2021mlperf",
        "authors": "Colby Banbury and Vijay Janapa Reddi and Peter Torelli and Jeremy Holleman and Nat Jeffries and Csaba Kiraly and Pietro Montino and David Kanter and Sebastian Ahmed and Danilo Pau and Urmish Thakker and Antonio Torrini and Peter Warden and Jay Cordaro and Giuseppe Di Guglielmo and Javier Duarte and Stephen Gibellini and Videet Parekh and Honson Tran and Nhan Tran and Niu Wenxu and Xu Xuesong",
        "authors_short": "Banbury et al.",
        "year": 2021,
        "title": "MLPerf Tiny Benchmark",
        "venue": "NeurIPS Datasets and Benchmarks Track",
        "volume": "",
        "number": "",
        "pages": "",
        "doi": "",
        "url": "https://openreview.net/forum?id=8RxxwAut1BI",
        "problem": "Reproducible comparison of ultra-low-power TinyML systems.",
        "dataset": "Keyword spotting, visual wake words, image classification, and machine-anomaly benchmarks.",
        "model": "Standardized reference models and benchmark rules.",
        "hardware": "Multiple ultra-low-power MCU-class systems.",
        "evaluation": "Accuracy, latency, and energy benchmarking.",
        "limitation": "No smart-meter load forecasting task or Python-to-export parity question.",
        "difference": "It defines stronger benchmarking norms; our timing/resource protocol is application-specific and still lacks measured energy per inference.",
        "table11": True,
        "temporal_evaluation": "Task-specific benchmark splits; not load forecasting",
        "anomaly_evidence": "Machine anomaly benchmark, not smart-meter events",
        "full_vector_parity": "Not its research question",
        "measured_cost": "Latency and energy benchmark framework",
        "bib_type": "inproceedings",
    },
    {
        "key": "lin2020mcunet",
        "authors": "Ji Lin and Wei-Ming Chen and Yujun Lin and John Cohn and Chuang Gan and Song Han",
        "authors_short": "Lin et al.",
        "year": 2020,
        "title": "MCUNet: Tiny Deep Learning on IoT Devices",
        "venue": "Advances in Neural Information Processing Systems",
        "volume": "33",
        "number": "",
        "pages": "11711--11722",
        "doi": "",
        "url": "https://papers.nips.cc/paper/2020/hash/86c51678350f656dcc7f490a43946ee5-Abstract.html",
        "problem": "Fitting and accelerating deep neural networks on microcontrollers.",
        "dataset": "ImageNet, visual wake words, and speech commands.",
        "model": "TinyNAS plus the TinyEngine inference library.",
        "hardware": "Off-the-shelf microcontrollers including STM32-class devices.",
        "evaluation": "Accuracy, SRAM, flash, and inference-speed comparisons.",
        "limitation": "No energy load forecasting or smart-meter anomaly study.",
        "difference": "Our linear model needs no neural runtime and answers an application-specific portability question, but it is not a general TinyML systems contribution.",
        "table11": False,
        "temporal_evaluation": "Not a time-series forecasting study",
        "anomaly_evidence": "None for energy systems",
        "full_vector_parity": "Not its research question",
        "measured_cost": "SRAM, flash, and latency",
        "bib_type": "inproceedings",
    },
    {
        "key": "hernandez2024daily",
        "authors": "{\\'A}lvaro Hern{\\'a}ndez and Rub{\\'e}n Nieto and Laura de Diego-Ot{\\'o}n and Mar{\\'i}a Carmen P{\\'e}rez-Rubio and Jos{\\'e} M. Villadangos-Carrizo and Daniel Pizarro and Jes{\\'u}s Ure{\\~n}a",
        "authors_short": "Hernández et al.",
        "year": 2024,
        "title": "Detection of Anomalies in Daily Activities Using Data from Smart Meters",
        "venue": "Sensors",
        "volume": "24",
        "number": "2",
        "pages": "515",
        "doi": "10.3390/s24020515",
        "url": "https://doi.org/10.3390/s24020515",
        "problem": "Prediction-based detection of unusual daily activities from household electricity use.",
        "dataset": "Seven months of hourly appliance data from a commercial Wibeee meter in one four-tenant household.",
        "model": "LSTM, CNN, random forest, and decision tree.",
        "hardware": "Commercial physical meter collected data; edge implementation is described as a future objective.",
        "evaluation": "Next-hour forecasting followed by alarm evaluation; LSTM recall 0.83 and F1 0.80.",
        "limitation": "Single household and application-specific activity alarms limit generalization.",
        "difference": "It has stronger real sensing and event context than our current data, while our contribution is exact MCU computation transfer and resource accounting.",
        "table11": True,
        "temporal_evaluation": "Seven-month household series; next-hour prediction",
        "anomaly_evidence": "Activity-alarm labels from an instrumented household",
        "full_vector_parity": "Not reported",
        "measured_cost": "Edge feasibility discussed; MCU cost not reported",
    },
    {
        "key": "aurangzeb2024bilstm",
        "authors": "Khursheed Aurangzeb and Syed Irtaza Haider and Musaed Alhussein",
        "authors_short": "Aurangzeb et al.",
        "year": 2024,
        "title": "Individual Household Load Forecasting Using Bi-Directional LSTM Network with Time-Based Embedding",
        "venue": "Energy Reports",
        "volume": "11",
        "number": "",
        "pages": "3963--3975",
        "doi": "10.1016/j.egyr.2024.03.028",
        "url": "https://doi.org/10.1016/j.egyr.2024.03.028",
        "problem": "Individual household short-term load forecasting and feature/loss selection.",
        "dataset": "Australian Smart Grid Smart City data; eight customers in the reported comparison.",
        "model": "T2V-BiLSTM and multiple recurrent/convolutional baselines.",
        "hardware": "No constrained-device implementation reported.",
        "evaluation": "RMSE/MAPE across households and seasons with feature-engineering comparisons.",
        "limitation": "Limited household/geographic coverage; no weather/occupancy factors; interpretability and long horizons remain open.",
        "difference": "It is a stronger model-comparison study; our contribution concerns tiny deployment fidelity rather than forecasting architecture novelty.",
        "table11": False,
        "temporal_evaluation": "Household/season forecasting comparison",
        "anomaly_evidence": "None",
        "full_vector_parity": "Not reported",
        "measured_cost": "No MCU cost reported",
    },
    {
        "key": "li2024federated",
        "authors": "Yehui Li and Dalin Qin and H. Vincent Poor and Yi Wang",
        "authors_short": "Li et al.",
        "year": 2024,
        "title": "Introducing Edge Intelligence to Smart Meters via Federated Split Learning",
        "venue": "Nature Communications",
        "volume": "15",
        "number": "1",
        "pages": "9044",
        "doi": "10.1038/s41467-024-53352-9",
        "url": "https://doi.org/10.1038/s41467-024-53352-9",
        "problem": "Privacy-enhancing distributed training for on-device load forecasting under meter constraints.",
        "dataset": "Building Data Genome 2 and Irish CER customer-behaviour data.",
        "model": "Federated split learning with MLP and CNN/RNN/GRU/LSTM backbones.",
        "hardware": "Thirty ARM Cortex-M4 MCUs plus three edge PCs and one cloud server.",
        "evaluation": "First year for training and following half-year for testing; five experiments with 95% CIs; memory, training time, and communication measured.",
        "limitation": "One representative meter hardware configuration and no anomaly-detection study.",
        "difference": "This is strong prior art for MCU load forecasting. Our distinct scope is simpler local inference on ESP8266 with explicit Python/C++/device parity and no claim of distributed training or privacy innovation.",
        "table11": True,
        "temporal_evaluation": "First year train; subsequent half-year test; five runs with 95% CIs",
        "anomaly_evidence": "None",
        "full_vector_parity": "Not reported as a Python/C++ parity audit",
        "measured_cost": "MCU memory, training time, communication",
    },
    {
        "key": "kolosov2025instrumental",
        "authors": "Dimitrios Kolosov and Matthew Robinson and Pascal A. Schirmer and Iosif Mporas",
        "authors_short": "Kolosov et al.",
        "year": 2025,
        "title": "An Instrumental High-Frequency Smart Meter with Embedded Energy Disaggregation",
        "venue": "Sensors",
        "volume": "25",
        "number": "17",
        "pages": "5280",
        "doi": "10.3390/s25175280",
        "url": "https://doi.org/10.3390/s25175280",
        "problem": "High-frequency smart-meter sensing with on-edge non-intrusive load monitoring.",
        "dataset": "Measured 15-kHz voltage/current/power signatures and NILM evaluation data.",
        "model": "Deep NILM regression with FP32/FP16/INT8 variants.",
        "hardware": "Custom analog front end plus six Raspberry Pi/accelerator/FPGA-class platforms.",
        "evaluation": "Measurement fidelity, accuracy, feature/model latency, throughput, power, energy efficiency, and cost efficiency.",
        "limitation": "Targets NILM on substantially stronger hardware, not low-rate forecasting/anomaly decisions on ESP8266.",
        "difference": "It provides the calibrated sensing and power evidence our current work lacks. Our present paper must remain an HIL portability study until a comparable sensing experiment exists.",
        "table11": True,
        "temporal_evaluation": "NILM train/test scenarios; not load forecasting",
        "anomaly_evidence": "None; appliance disaggregation task",
        "full_vector_parity": "Cross-platform accuracy, not row-wise export parity",
        "measured_cost": "Latency, power, throughput, efficiency across six boards",
    },
]


def bibtex(study: dict[str, object]) -> str:
    kind = study.get("bib_type", "article")
    fields = [
        ("author", study["authors"]),
        ("title", "{" + str(study["title"]) + "}"),
    ]
    if kind == "article":
        fields.append(("journal", study["venue"]))
    else:
        fields.append(("booktitle", study["venue"]))
    fields.append(("year", study["year"]))
    for source, target in [("volume", "volume"), ("number", "number"), ("pages", "pages"), ("doi", "doi")]:
        if study.get(source):
            fields.append((target, study[source]))
    fields.append(("url", study["url"]))
    body = ",\n".join(f"  {name} = {{{value}}}" for name, value in fields)
    return f"@{kind}{{{study['key']},\n{body}\n}}"


def main() -> None:
    OUTPUTS.mkdir(exist_ok=True)
    TABLES.mkdir(exist_ok=True)
    REFERENCES.mkdir(exist_ok=True)

    record = {
        "phase": 23,
        "review_type": "targeted peer-reviewed gap analysis; not a systematic review",
        "search_date": date.today().isoformat(),
        "search_scope": [
            "smart-meter and household load forecasting",
            "prediction-based smart-meter anomaly detection",
            "edge intelligence for energy systems",
            "TinyML benchmarking and model compression",
            "physical embedded smart-meter and NILM validation",
        ],
        "sources_consulted": [
            "IEEE Xplore and IEEE-linked institutional records",
            "ScienceDirect",
            "Springer Nature / Nature Communications",
            "MDPI Sensors",
            "NeurIPS proceedings and OpenReview",
            "Crossref DOI metadata",
        ],
        "inclusion_rule": "Peer-reviewed publication directly relevant to at least one search scope, with bibliographic metadata and technical claims checked on a publisher, proceedings, DOI, or accepted-manuscript page.",
        "exclusion_rule": "Unverified blogs, student reports, preprints lacking a confirmed peer-reviewed venue, and studies whose relevance could not be established from a primary or accepted source.",
        "novelty_conclusion": "The broad idea is not unique. Forecasting, residual anomaly detection, edge smart-meter analytics, MCU load forecasting, and physical embedded NILM all have prior art. The defensible differentiator is the documented combination of a nine-parameter ESP8266 model, generated Python-to-C++ transfer, complete 933-vector numerical and threshold-decision parity, and explicit IRAM/RAM/flash/timing accounting.",
        "prohibited_claim": "Do not claim first smart-meter TinyML, first edge load forecasting, first ESP-class energy ML, or first embedded anomaly detection.",
        "studies": STUDIES,
    }
    (OUTPUTS / "phase23_related_work.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    columns = ["Citation key", "Study", "Problem", "Dataset", "Model", "Hardware", "Evaluation", "Limitation", "Difference from this work", "Verified URL", "Table 11"]
    with (TABLES / "phase23_related_work_matrix.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for study in STUDIES:
            writer.writerow([
                study["key"], f"{study['authors_short']} ({study['year']})", study["problem"], study["dataset"],
                study["model"], study["hardware"], study["evaluation"], study["limitation"], study["difference"],
                study["url"], "yes" if study["table11"] else "supporting only",
            ])

    bib = "% Curated and DOI-checked for Phase 23 on 2026-09-03.\n\n" + "\n\n".join(bibtex(study) for study in STUDIES) + "\n"
    (REFERENCES / "references.bib").write_text(bib, encoding="utf-8")

    print(f"Wrote {len(STUDIES)} verified related-work records.")
    print(f"Table 11 studies: {sum(bool(s['table11']) for s in STUDIES)}")
    print("results/phase23_related_work.json")
    print("tables/phase23_related_work_matrix.csv")
    print("references/references.bib")


if __name__ == "__main__":
    main()
