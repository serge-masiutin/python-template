export type User = { id: string; username: string; admin: boolean };
export type Note = { id: string; body: string };
export type SharedProps = { auth: { user: User | null }; csrfToken: string };
export type FlashData = { messages?: { level: string; message: string }[] };
declare module "@inertiajs/core" {
  interface InertiaConfig {
    sharedPageProps: SharedProps;
    flashDataType: FlashData;
    errorValueType: string;
  }
}
