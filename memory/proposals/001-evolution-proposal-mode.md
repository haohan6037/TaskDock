# Proposal 001: Evolution Proposal Mode

Status: approved

Approved by: human

Approved at: 2026-06-03

## Goal

Add a required proposal workflow before adding or changing OpenClaw Brain capabilities.

## Motivation

OpenClaw Brain should evolve gradually with human approval. To avoid uncontrolled self-modification, every new capability should first be described as a proposal, reviewed by the human, and only implemented after approval.

## Proposed Change

Use `memory/proposals/` as the project location for capability proposals.

Each proposal should include:

- title
- status: proposed / approved / rejected / implemented
- goal
- motivation
- proposed files to change
- risk level
- validation plan
- approval note

## First Use

Use this proposal mode before adding:

- doc-worker
- dispatcher routing improvements
- OpenClaw-to-dispatcher integration
- memory retrieval upgrades
- worker verification logic

## Minimal Implementation

1. Create `memory/proposals/`.
2. Add this approved proposal.
3. Add a decision memory entry saying future new capabilities require approved proposals.
4. Do not change runtime behavior yet.

## Risk

Low. This only adds governance documentation and does not affect the running dispatcher or workers.

## Validation

Confirm that future capability changes can reference an approved proposal before implementation.
