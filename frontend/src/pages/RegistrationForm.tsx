import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { useNavigate } from "react-router-dom";
import { useApi } from "../hooks/useAPI";
import { Store } from "../store/Store";
import { setStoredUser } from "../lib/session";
import type { RegisterResponse } from "../types/api";

const formSchema = z
  .object({
    email: z.string().email("Введіть коректну email адресу"),
    password: z.string().min(8, "Пароль має містити щонайменше 8 символів"),
    confirmPassword: z.string().min(8, "Пароль має містити щонайменше 8 символів"),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Паролі не співпадають",
    path: ["confirmPassword"],
  });

type FormData = z.infer<typeof formSchema>;

export default function RegistrationForm() {
  const { post } = useApi();
  const { error } = Store();
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    mode: "onBlur",
  });

  const onSubmit = async (data: FormData) => {
    const result = await post<RegisterResponse>("/api/auth/register", {
      email: data.email,
      password: data.password,
      confirmPassword: data.confirmPassword,
    });

    if (result) {
      setStoredUser({ id: result.id, email: result.email });
      navigate("/home");
    }
  };

  return (
    <div className="relative min-h-screen w-screen bg-[#2f2f2f] overflow-hidden font-sans">
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute left-0 top-0 h-full w-[55%]">
          <div
            className="absolute inset-0 bg-[#1f4fb2]"
            style={{ clipPath: "polygon(0 0, 100% 0, 0 100%)" }}
          />
          <div
            className="absolute inset-0 bg-[#8fb5ff]"
            style={{ clipPath: "polygon(0 0, 100% 50%, 0 100%)" }}
          />
          <div
            className="absolute inset-0 bg-[#f28c28]"
            style={{ clipPath: "polygon(0 100%, 100% 100%, 100% 50%)" }}
          />
        </div>
      </div>

      <div className="relative flex min-h-screen items-center justify-end px-12 md:px-20">
        <div className="w-full max-w-md text-white">
          <div className="mb-8 text-center text-2xl font-semibold">Sign up</div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div className="space-y-2">
              <label className="text-xs text-[#b6b6b6]">E-mail</label>
              <input
                {...register("email")}
                type="email"
                placeholder="user.email@gmail.com"
                className={`h-11 w-full rounded-md border bg-[#3b3b3b] px-3 text-sm outline-none transition ${errors.email
                  ? "border-red-400"
                  : "border-transparent focus:border-[#f28c28]"
                  }`}
              />
              {errors.email && (
                <p className="text-xs text-red-400">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-xs text-[#b6b6b6]">Password</label>
              <input
                {...register("password")}
                type="password"
                placeholder="********"
                className={`h-11 w-full rounded-md border bg-[#3b3b3b] px-3 text-sm outline-none transition ${errors.password
                  ? "border-red-400"
                  : "border-transparent focus:border-[#f28c28]"
                  }`}
              />
              {errors.password && (
                <p className="text-xs text-red-400">{errors.password.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-xs text-[#b6b6b6]">Confirm password</label>
              <input
                {...register("confirmPassword")}
                type="password"
                placeholder="********"
                className={`h-11 w-full rounded-md border bg-[#3b3b3b] px-3 text-sm outline-none transition ${errors.confirmPassword
                  ? "border-red-400"
                  : "border-transparent focus:border-[#f28c28]"
                  }`}
              />
              {errors.confirmPassword && (
                <p className="text-xs text-red-400">{errors.confirmPassword.message}</p>
              )}
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="h-11 w-full rounded-md bg-[#f28c28] text-sm font-semibold text-white transition hover:bg-[#e57f1b] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isSubmitting ? "Signing up..." : "Sign up"}
            </button>
            {error && <p className="text-xs text-red-400">{error}</p>}
          </form>

          <div className="my-6 flex items-center gap-3 text-xs text-[#9a9a9a]">
            <div className="h-px flex-1 bg-[#4a4a4a]" />
            <span>or</span>
            <div className="h-px flex-1 bg-[#4a4a4a]" />
          </div>

          <div className="space-y-3">
            <button
              type="button"
              className="flex h-10 w-full items-center justify-center gap-2 rounded-md bg-[#3b3b3b] text-sm text-white"
            >
              <span className="flex h-5 w-5 items-center justify-center rounded-full bg-white text-xs font-bold text-[#ea4335]">
                G
              </span>
              Sign up with Google
            </button>
            <button
              type="button"
              className="flex h-10 w-full items-center justify-center gap-2 rounded-md bg-[#3b3b3b] text-sm text-white"
            >
              <span className="flex h-5 w-5 items-center justify-center rounded bg-white text-[10px] font-bold text-[#1f4fb2]">
                M
              </span>
              Sign up with Microsoft
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
