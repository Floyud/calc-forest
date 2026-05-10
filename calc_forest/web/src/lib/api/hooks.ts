import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getClassForest,
  getClassSummary,
  getCurrentCycle,
  getStudentProfile,
  getTreeSpecies,
  getSessionDraft,
  patchStudentProfile,
} from "@/lib/api";
import type { DifySessionDraftRequest } from "@/lib/types";

export function useClassForest(classId: string) {
  return useQuery({
    queryKey: ["classForest", classId],
    queryFn: () => getClassForest(classId),
  });
}

export function useClassSummary(classId: string) {
  return useQuery({
    queryKey: ["classSummary", classId],
    queryFn: () => getClassSummary(classId),
  });
}

export function useStudentProfile(studentId: string) {
  return useQuery({
    queryKey: ["studentProfile", studentId],
    queryFn: () => getStudentProfile(studentId),
  });
}

export function useCurrentCycle(grade: number) {
  return useQuery({
    queryKey: ["currentCycle", grade],
    queryFn: () => getCurrentCycle(grade),
  });
}

export function useTreeSpecies() {
  return useQuery({
    queryKey: ["treeSpecies"],
    queryFn: getTreeSpecies,
    staleTime: 5 * 60_000,
  });
}

export function useSessionDraft() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: DifySessionDraftRequest) => getSessionDraft(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["classForest"] });
    },
  });
}

export function useUpdateStudentProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      studentId,
      data,
    }: {
      studentId: string;
      data: { personality_tags?: string[]; learning_style?: string; notes?: string };
    }) => patchStudentProfile(studentId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["studentProfile", variables.studentId] });
      queryClient.invalidateQueries({ queryKey: ["classForest"] });
    },
  });
}
