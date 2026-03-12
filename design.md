# このファイルはプロジェクトのコア設計を説明するためのものです。

# Copilotがこのファイルを参照することで実装を補助することを目的としています。

#

# =========================================================

# このプロジェクトの目的

# =========================================================

#

# このプロジェクトはAI処理をパイプラインとして実行するための

# 「AI Workflow Engine」を提供する。

#

# 主な用途

#

# - 動画生成

# - face swap

# - voice swap

# - データ生成パイプライン

#

# 各処理は「Node」として定義される。

# NodeはPipeline内で順番に実行される。

#

#

# =========================================================

# 基本概念

# =========================================================

#

# Pipeline

# Nodeを順番に実行する処理単位

#

# Node

# パイプラインの1つの処理

#

# Context

# Node間で共有される実行状態

#

# Artifact

# Nodeの出力データ

#

# ArtifactRepository

# Artifactの保存・取得を担当する

#

#

# =========================================================

# Pipeline 実行の流れ

# =========================================================

#

# 1 PipelineDefinitionを取得

#

# 2 NodeFactoryがNodeを生成

#

# 3 Pipelineを構築

#

# 4 Contextを作成

#

# 5 Pipeline.run()を実行

#

#

# 実行イメージ

#

# VideoInputNode

# ↓

# FrameExtractNode

# ↓

# FaceSwapNode

# ↓

# RenderNode

#

#

# =========================================================

# Node設計ルール

# =========================================================

#

# Nodeは以下を必ず宣言する

#

# inputs

# 必要なArtifact名

#

# outputs

# 出力するArtifact名

#

# NodeはArtifactRepositoryを通してデータを保存する。

#

# NodeはContextからArtifactを取得する。

#

#

# =========================================================

# Artifact設計

# =========================================================

#

# Artifactは直接データを持たない。

#

# ContextにはArtifactIDのみを保存する。

#

# data -> repository -> artifact_id

#

# 例

#

# context.artifacts = {

# "video": "artifact_1",

# "frames": "artifact_2"

# }

#

#

# =========================================================

# ArtifactRepository

# =========================================================

#

# ArtifactRepositoryはデータ保存を抽象化する。

#

# 将来的に以下を切り替える可能性がある

#

# - ローカルファイルシステム

# - S3

# - MinIO

# - Redis

# - データベース

#

#

# =========================================================

# Node Registry

# =========================================================

#

# Nodeはregistryに登録される。

#

# register_node("frame_extract", FrameExtractNode)

#

# PipelineDefinitionにはnode_typeが保存される。

#

# NodeFactoryはnode_typeからNodeを生成する。

#

#

# =========================================================

# PipelineDefinition

# =========================================================

#

# PipelineはDBまたは設定から定義される。

#

# PipelineDefinition

#

# id

# nodes[]

#

# NodeDefinition

#

# type

# config

# order

#

#

# =========================================================

# 拡張方針

# =========================================================

#

# 将来追加予定

#

# - node plugin system

# - pipeline graph UI

# - distributed execution

# - GPU node

#

#

# この設計は

#

# Airflow

# Kubeflow

# ComfyUI

#

# の中間的な構造を目指す。
